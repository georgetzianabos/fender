from microbit import (  # pylint: disable=import-error
    display, sleep, i2c, Image, pin1, pin2, pin15, accelerometer
)
import machine  # pylint: disable=import-error
import utime  # pylint: disable=import-error
import neopixel  # pylint: disable=import-error

import random

LEFT_MOTOR = 0x00
RIGHT_MOTOR = 0x02

FORWARDS = 0x00
BACKWARDS = 0x01


class Maqueen:

    def __init__(self):

        self.np = neopixel.NeoPixel(pin15, 4)

    def read_distance(self):

        self.motor_stop(LEFT_MOTOR)
        self.motor_stop(RIGHT_MOTOR)

        divider = 42
        maxtime = 250 * divider

        pin2.read_digital()
        pin1.write_digital(0)
        utime.sleep_us(2)
        pin1.write_digital(1)
        utime.sleep_us(10)
        pin1.write_digital(0)

        duration = machine.time_pulse_us(pin2, 1, maxtime)
        distance = duration / divider

        color = (0, 255, 0)

        if distance <= 35:
            color = (255, 0, 0)
        elif distance > 35 and distance < 50:
            color = (255, 128, 0)

        for led in range(4):
            self.np[led] = color

        self.np.show()

        return distance

    def motor_run(self, motor, direction, speed):

        speed = 255 if speed > 255 else speed
        speed = 0 if speed < 0 else speed

        buffer = bytearray([motor, direction, speed])

        try:
            i2c.write(0x10, buffer)
        except OSError:
            display.show(Image.SAD)

    def motor_stop(self, motor):

        buffer = bytearray([motor, FORWARDS, 0])

        try:
            i2c.write(0x10, buffer)
        except OSError:
            display.show(Image.SAD)


STATE_MOVING = 0
STATE_FIND_CLEARING = 1
STATE_REVERSE = 2


class Robot:

    def __init__(self):

        self.state = STATE_FIND_CLEARING
        self.maqueen = Maqueen()

    def upright_check(self):

        upright = False

        for _ in range(3):

            reading = accelerometer.get_y()

            upright = reading > 800

            if upright:
                break

            self.maqueen.motor_stop(LEFT_MOTOR)
            self.maqueen.motor_stop(RIGHT_MOTOR)

            sleep(100)

        if not upright:
            self.state = STATE_REVERSE

    def moving(self):

        display.show(Image.HAPPY)

        while self.state == STATE_MOVING:

            distance = self.maqueen.read_distance()

            self.maqueen.motor_run(LEFT_MOTOR, FORWARDS, 100)
            self.maqueen.motor_run(RIGHT_MOTOR, FORWARDS, 100)

            sleep(100)

            if distance < 35 and distance is not 0:
                self.state = STATE_FIND_CLEARING

            self.upright_check()

    def find_clearing(self):

        display.show(Image.CONFUSED)

        direction = random.choice([True, False])

        attempts = 0

        while self.state == STATE_FIND_CLEARING:

            attempts += 1
            if attempts > 30:
                direction = not direction
                attempts = 0

            distance = self.maqueen.read_distance()

            if direction:
                self.maqueen.motor_run(LEFT_MOTOR, FORWARDS, 50)
                self.maqueen.motor_run(RIGHT_MOTOR, BACKWARDS, 50)
            else:
                self.maqueen.motor_run(LEFT_MOTOR, BACKWARDS, 50)
                self.maqueen.motor_run(RIGHT_MOTOR, FORWARDS, 50)

            sleep_for = 200 if attempts > 60 else 100

            sleep(sleep_for)

            if distance > 50 and distance is not 0:
                self.state = STATE_MOVING

            self.upright_check()

    def reverse(self):

        self.maqueen.motor_run(LEFT_MOTOR, BACKWARDS, 100)
        self.maqueen.motor_run(RIGHT_MOTOR, BACKWARDS, 100)

        sleep(2000)

        self.maqueen.motor_run(LEFT_MOTOR, BACKWARDS, 50)
        self.maqueen.motor_run(RIGHT_MOTOR, FORWARDS, 50)

        sleep(1000)

        self.state = STATE_FIND_CLEARING

    def run(self):

        while True:

            if self.state == STATE_REVERSE:
                self.reverse()

            if self.state == STATE_MOVING:
                self.moving()

            if self.state == STATE_FIND_CLEARING:
                self.find_clearing()

robot = Robot()

robot.run()
