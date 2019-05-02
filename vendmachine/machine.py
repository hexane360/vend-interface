import RPi.GPIO as GPIO
import time
from enum import IntEnum

GPIO.setmode(GPIO.BCM)
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

class Machine():
	def __init__(self):
		self.drivers = Drivers()

		GPIO.setup(acceptingPin, GPIO.OUT, initial=GPIO.HIGH)
		GPIO.setup(pulsePin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(oosPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		GPIO.setup(irPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(irPin, GPIO.BOTH, callback=irEvent)

	def pulseEvent(self, callback):
		GPIO.add_event_detect(pulsePin, GPIO.FALLING, callback=callback, bouncetime=20) #20 ms
	def oosEvent(self, callback):
		def shim(channel):
			callback(GPIO.input(channel) == True)
		GPIO.add_event_detect(oosPin, GPIO.BOTH, callback=shim, bouncetime=50) #50 ms
	def vend(self, motor):
		if motor < 0 or motor > 2*len(sleepPins)-1:
			raise ValueError("Invalid motor # {}".format(motor))
		if GPIO.input(irPin):
			raise ValueError("IR beam broken")
		self.drivers.wake_on(motor >> 1) #which driver to run
		if motor%2:                      #left or right motor on driver
			self.drivers.dir(Dir.Stop, Dir.CW)
		else:
			self.drivers.dir(Dir.CW, Dir.Stop)
		self.drivers.run(255)
		result = GPIO.wait_for_edge(irPin, GPIO_RISING, timeout=30000, bouncetime=10)
		self.drivers.stop()
		if result is None:
			raise ValueError("Product not detected")
	def cleanup(self):
		GPIO.cleanup()

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
	def reset(self):
		GPIO.output(resetPin, False)
		time.sleep(50.0/1000000.0) #50 us
		GPIO.output(resetPin, True)
		self._dirA = Dir.CW
		self._dirB = Dir.CW
		self._step = 1
	def restep(self):
		GPIO.output(resetPin, False)
		time.sleep(50.0/1000000.0) #50 us
		GPIO.output(resetPin, True)
		step = self._step
		self._step = 1
		self.step_to(step)
	def run(self, speed):
		self._speed = speed
		if self._dirA != Dir.Stop or self._dirB != Dir.Stop:
			self._setSpeed(speed)
	def stop(self):
		self.run(0)

	def sleep(self, driver, sleep=True):
		if driver < 0 or driver >= len(sleepPins):
			raise ValueError("Driver out of range")
		if self._sleep[driver] == sleep:
			return
		self._sleep[driver] = sleep
		GPIO.output(sleepPins[driver], not sleep)
		time.sleep(1.7/1000.0) #1.7 ms
		self.restep()
	def sleep_arr(self, sleep_arr):
		changed = False
		for i, old, new in zip(self._sleep, sleep_arr):
			if old != new:
				old = new
				changed = True
		if changed:
			time.sleep(1.7/1000.0) #1.7 ms
			self.restep()
	def wake_one(self, driver):
		changed = False
		for i, slept in enumerate(self._sleep):
			if i == driver:
				if slept:
					self._sleep[i] = False
					changed = True
			else:
				if not slept:
					self._sleep[i] = True
					changed = True
		if changed:
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
			_stepTo(0 if dirA > 0 else 4)
		elif dirB == Dir.CW:
			_stepTo(2 - dirA)
		else:
			_stepTo(6 + dirA)
		if setSpeed:
			self._setSpeed(self._speed)

	def _stepTo(self, end):
		self._stepN(end + (8 if end < self._step else 0) - self._step)
	def _stepN(self, num):
		for i in range(num):
			GPIO.output(stepPin, False)
			time.sleep(20.0/1000.0) #20 ms
			GPIO.output(stepPin, True)
			time.sleep(20.0/1000.0) #20 ms
		self._step = (self._step + num)%8
	def _setSpeed(self, speed):
		if speed > 100.0:
			speed = 100.0
		if speed < 0.0:
			speed = 0.0
		self._pwm.ChangeDutyCycle(100.0 - speed)
