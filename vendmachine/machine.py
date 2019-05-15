try:
	import RPi.GPIO as GPIO
	simulated = False
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
except ModuleNotFoundError: #Server handles actual simulation
	pass

import time
from enum import IntEnum

#motor pins (BCM designation)
enablePin = 18 #pwm
resetPin = 23
stepPin = 24
sleepPins = [25,8,7,1]

#bill pins
acceptingPin = 27 #enable pin
pulsePin = 17
oosPin = 22 #out of service

#ir pin
irPin = 12

def irEvent(channel):
	if GPIO.input(channel):
		print("IR: 1")
	else:
		print("IR: 0")

#class to monitor a GPIO pin and return debounced events
#returns events at time of *next* edge
class Monitor():
	def __init__(self, pin, debounce=20, **kwargs):
		self._pin = pin
		self.debounce = 20
		GPIO.setup(pin, GPIO.IN, **kwargs)
		self._t = time.monotonic_ns()
		self._state = GPIO.input(pin)
		self._callbacks = []
		GPIO.add_event_detect(pin, GPIO.BOTH, callback=self._callback)
	def _callback(self, channel):
		state = GPIO.input(self._pin)
		if state == self._state:
			return
		self._state = state
		t = time.monotonic_ns()
		delta = t - self._t
		self._t = t
		print("Got pulse event: {}".format(state))
		print("Time difference: {} ms".format(delta/1000000))
		if (delta > self.debounce*1000000):
			for cb in self._callbacks:
				cb(not self._state) #return pulse that just ended
	def register(self, callback):
		self._callbacks.append(callback)

class Machine():
	def __init__(self):
		self.drivers = Drivers()

		GPIO.setup(acceptingPin, GPIO.OUT, initial=GPIO.HIGH)
		GPIO.setup(oosPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		self._oos = GPIO.input(oosPin) == True
		self._pulse = Monitor(pulsePin, pull_up_down = GPIO.PUD_UP)

		GPIO.setup(irPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		#GPIO.add_event_detect(irPin, GPIO.BOTH, callback=irEvent)

	def pulseEvent(self, callback):
		def shim(val):
			if not val:
				callback()
		self._pulse.register(shim)

	def accepting(self, value):
		GPIO.output(acceptingPin, value)

	def oosEvent(self, callback):
		def shim(channel):
			oos = GPIO.input(channel) == True
			if self._oos != oos:
				self._oos = oos
				callback(oos)
		GPIO.add_event_detect(oosPin, GPIO.BOTH, callback=shim, bouncetime=50) #50 ms
	def vend(self, motor):
		print("Vending on motor {}".format(motor))
		if motor < 0 or motor > 2*len(sleepPins)-1:
			raise ValueError("Invalid motor # {}".format(motor))
		if not GPIO.input(irPin):
			raise ValueError("IR beam broken")
		self.drivers.wake_one(motor >> 1) #which driver to run
		if motor%2:                      #left or right motor on driver
			self.drivers.dir(Dir.Stop, Dir.CW)
		else:
			self.drivers.dir(Dir.CW, Dir.Stop)
		print("Running motor")
		self.drivers.run(255)
		result = GPIO.wait_for_edge(irPin, GPIO.FALLING, timeout=3000, bouncetime=10)
		self.drivers.stop()
		if result is None:
			raise ValueError("Product not detected")
		print("Vend successful")
	def stop(self):
		self.drivers.stop()
		GPIO.remove_event_detect(oosPin)
		GPIO.remove_event_detect(pulsePin)
		GPIO.remove_event_detect(irPin)
		GPIO.output(acceptingPin, GPIO.LOW) #disable acceptor
		#GPIO.cleanup()

class Dir(IntEnum):
	CCW = -1
	Stop = 0
	CW = 1

"""
STEP MAP: (+ is CW) (A is near supply, +s are on outside)
step:   A:   B:
   0:  100    0
   1:   71   71  START POS
   2:    0  100
   3:  -71   71
   4: -100    0
   5:  -71  -71
   6:    0 -100
   7:   71  -71
"""

class Drivers():
	def __init__(self):
		self._dirA = Dir.CW
		self._dirB = Dir.CW
		self._step = 1
		self._slept = [True]*len(sleepPins)
		GPIO.setup(enablePin, GPIO.OUT)
		self._pwm = GPIO.PWM(enablePin, 100)
		self._pwm.start(100.0)
		GPIO.setup(resetPin, GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(stepPin, GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(sleepPins, GPIO.OUT, initial=GPIO.LOW) #high to wake
		GPIO.output(stepPin, True)
	def __del__(self):
		GPIO.output(resetPin, False) #deactivate drivers
		self._setSpeed(0) #stop PWM
	def reset(self):
		GPIO.output(resetPin, False)
		time.sleep(50.0/1000000.0) #50 us
		GPIO.output(resetPin, True)
		self._stepN(1) #gets drivers ready for step commands
		self._dirA = Dir.CW
		self._dirB = Dir.CW
		self._step = 1
	def restep(self):
		GPIO.output(resetPin, False)
		time.sleep(50.0/1000000.0) #50 us
		GPIO.output(resetPin, True)
		step = self._step
		self._step = 1
		self._stepTo(step)
	def run(self, speed):
		self._speed = speed
		if self._dirA != Dir.Stop or self._dirB != Dir.Stop:
			self._setSpeed(speed)
	def stop(self):
		self.run(0)

	def sleep(self, driver, sleep=True):
		if driver < 0 or driver >= len(sleepPins):
			raise ValueError("Driver out of range")
		if self._slept[driver] == sleep:
			return
		self._slept[driver] = sleep
		GPIO.output(sleepPins[driver], not sleep)
		time.sleep(1.7/1000.0) #1.7 ms
		self.restep()
	def sleep_arr(self, sleep_arr):
		changed = False
		for i, (old, new) in enumerate(zip(self._slept, sleep_arr)):
			if old != new:
				GPIO.output(sleepPins[i], not new)
				old = new
				changed = True
		if changed:
			time.sleep(1.7/1000.0) #1.7 ms
			self.restep()
	def wake_one(self, driver):
		changed = False
		for i, slept in enumerate(self._slept):
			if i == driver:
				if slept:
					GPIO.output(sleepPins[i], True)
					self._slept[i] = False
					changed = True
			else:
				if not slept:
					GPIO.output(sleepPins[i], False)
					self._slept[i] = True
					changed = True
		if changed or True: #just always restep to increase consistency
			time.sleep(1.7/1000.0) #1.7 ms
			self.restep()

	def dirA(self, d):
		self.dir(d, self._dirB)
	def dirB(self, d):
		self.dir(self._dirA, d)
	def dir(self, dirA, dirB):
		setSpeed = not self._dirA and not self._dirB and (dirA or dirB)
		self._dirA = dirA
		self._dirB = dirB
		if not dirA and not dirB:
			self._setSpeed(0)
		elif not dirB:
			self._stepTo(0 if dirA > 0 else 4)
		elif dirB == Dir.CW:
			self._stepTo(2 - dirA)
		else:
			self._stepTo(6 + dirA)
		if setSpeed:
			self._setSpeed(self._speed)

	def _stepTo(self, end):
		self._stepN(end + (8 if end < self._step else 0) - self._step)
	def _stepN(self, num):
		for i in range(2*num): #double because drivers are actually quarter stepping
			GPIO.output(stepPin, False)
			time.sleep(20.0/1000000.0) #20 us
			GPIO.output(stepPin, True)
			time.sleep(20.0/1000000.0) #20 us
		self._step = (self._step + num)%8
	def _setSpeed(self, speed):
		if speed > 100.0:
			speed = 100.0
		if speed < 0.0:
			speed = 0.0
		self._pwm.ChangeDutyCycle(100.0 - speed)
