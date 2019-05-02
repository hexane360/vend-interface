import RPIO
import time
from enum import IntEnum

#motor pins (BCM designation)
enablePin = 18 #pwm
resetPin = 23
stepPin = 24
sleepPins = [25,8,7,1]

#bill pins
acceptingPin = 5 #enable pin
pulsePin = 5
oosPin = 5 #out of service

#ir pin
irPin = 5

vending = False
caught = False

class Machine():
	def __init__(self):
		self.drivers = Drivers()

		RPIO.setup(acceptingPin, RPIO.OUT, initial=RPIO.HIGH)
		RPIO.setup(pulsePin, RPIO.IN)
		RPIO.setup(oosPin, RPIO.IN)
		
		RPIO.setup(irPin, RPIO.IN)
		RPIO.add_interrupt_callback(irPin, _vend_callback, edge='falling')
	def pulseEvent(callback):
		RPIO.add_interrupt_callback(pulsePin, callback, edge='falling', threaded_callback=True, debounce_timeout_ms=None)
	def oosEvent(callback):
		RPIO.add_interrupt_callback(pulsePin, callback, edge='both', threaded_callback=True, debounce_timeout_ms=None)
	def activateInterrupts():
		RPIO.wait_for_interrupts(threaded=True)

	def vend(motor):
		if motor < 0 or motor > 2*len(sleepPins)-1:
			raise ValueError("Invalid motor # {}".format(motor))
		if RPIO.input(irPin):
			raise ValueError("IR beam broken")
		self.drivers.wake_on(motor >> 1) #which driver to run
		if motor%2:                      #left or right motor on driver
			self.drivers.dir(Dir.Stop, Dir.CW)
		else:
			self.drivers.dir(Dir.CW, Dir.Stop)
		self.drivers.run(255)
		vending = True
		caught = False
		RPIO.wait_for_interrupts(epoll_timeout=30)
		vending = False
		RPIO.wait_for_interrupts(threaded=True) #immediately reenable non-blocking
		self.drivers.stop()
		if not self._caught:
			raise ValueError("Product not detected")
	def cleanup():
		RPIO.cleanup()

def _vend_callback(gpio, val):
	if not vending:
		return
	RPIO.stop_waiting_for_interrupts()
	caught = True

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
		self._pwm = RPIO.PWM.Servo()
		self._pwm.set_servo(18, 20000) #disable PWM
		RPIO.setup(resetPin, RPIO.OUT, initial=RPIO.LOW)
		RPIO.setup(stepPin, RPIO.OUT, initial=RPIO.LOW)
		for p in sleepPins:
			RPIO.setup(p, RPIO.OUT, initial=RPIO.LOW) #high to wake
		RPIO.output(stepPin, True)
	def reset(self):
		RPIO.output(resetPin, False)
		time.sleep(50.0/1000000.0) #50 us
		RPIO.output(resetPin, True)
		self._dirA = Dir.CW
		self._dirB = Dir.CW
		self._step = 1
	def restep(self):
		RPIO.output(resetPin, False)
		time.sleep(50.0/1000000.0) #50 us
		RPIO.output(resetPin, True)
		step = self._step
		self._step = 1
		self.step_to(step)
	def run(speed):
		self._speed = speed
		if self._dirA != Dir.Stop or self._dirB != Dir.Stop:
			self._setSpeed(speed)
	def stop():
		self.run(0)

	def sleep(driver, sleep=True):
		if driver < 0 or driver >= len(sleepPins):
			raise ValueError("Driver out of range")
		if self._sleep[driver] == sleep:
			return
		self._sleep[driver] = sleep
		RPIO.output(sleepPins[driver], not sleep)
		time.sleep(1.7/1000.0) #1.7 ms
		self.restep()
	def sleep_arr(sleep_arr):
		changed = False
		for i, old, new in zip(self._sleep, sleep_arr):
			if old != new:
				old = new
				changed = True
		if changed:
			time.sleep(1.7/1000.0) #1.7 ms
			self.restep()
	def wake_one(driver):
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
		
	def dirA(d):
		self.dir(d, self._dirB)
	def dirB(d):
		self.dir(self._dirA, d)
	def dir(dirA, dirB):
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

	def _stepTo(end):
		self._stepN(end + (8 if end < self._step else 0) - self._step)
	def _stepN(num):
		for i in range(num):
			RPIO.output(stepPin, False)
			time.sleep(20.0/1000.0) #20 ms
			RPIO.output(stepPin, True)
			time.sleep(20.0/1000.0) #20 ms
		self._step = (self._step + num)%8
	def _setSpeed(speed):
		if speed > 255:
			speed = 255
		if speed < 0:
			speed = 0
		self._pwm.set_servo(18, 20000 - speed*20000/255)
