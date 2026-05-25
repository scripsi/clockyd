from machine import Pin
import os
from time import sleep

# RGB LED at the back
red_led = Pin(4, Pin.OUT)
green_led = Pin(16, Pin.OUT)
blue_led = Pin(17, Pin.OUT)

# Cycle the rear LEDs on startup then turn them off
# (they are active low, so they work with inverted logic)
# Example: red_led.on() command turns the red LED off
green_led.on()
blue_led.on()
red_led.off()
sleep(0.5)
red_led.on()
green_led.off()
sleep(0.5)
green_led.on()
blue_led.off()
sleep(0.5)
blue_led.on()



