# ClockYD
# main.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2026 Douglas Reed

# *** IMPORTS ***

# Initialise nanogui hardware and framebuf before importing other modules.
from color_setup import ssd  # Create a display instance
from gui.core.nanogui import refresh
refresh(ssd, True)  # Initialise and clear display.

# Standard library modules
from machine import Pin, ADC, PWM
import time
import ntptime
import json
import network
import math

# Nanogui modules
from gui.widgets.label import Label
from gui.widgets.textbox import Textbox
from gui.core.writer import CWriter
from gui.core.colors import *
import gui.fonts.arial10 as small_font
import gui.fonts.paperr50 as large_font

# *** GLOBAL CONSTANTS ***

# Colours
TEAL=create_color(12,0,80,80)
screen_bg = BLACK
clock_fg = BLACK
clock_bg = TEAL
info_fg = GREY
info_bg = BLACK

# Clock dial dimensions
clock_face_r = 60
clock_index_r = 20
clock_index_inner_r = 10
clock_h_x = 80
clock_h_y = 80
clock_m_x = 240
clock_m_y = clock_h_y
clock_pos_y = 20

# *** GLOBAL CONFIG ***

config={}

# backlight control for screen
backlight = Pin(21, Pin.OUT)
backlight_pwm = PWM(backlight)

# LDR next to screen
light_sensor = ADC(34, atten=ADC.ATTN_0DB)

# RGB LEDs at the back
# (they are active low, so they work with inverted logic)
# Example: red_led.on() command turns the red LED off
red_led = Pin(4, Pin.OUT)
green_led = Pin(16, Pin.OUT)
blue_led = Pin(17, Pin.OUT)

# WiFi
wlan = network.WLAN(network.STA_IF)

# Text labels
CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
info_wri = CWriter(ssd, small_font, info_fg, info_bg, verbose=False)
clock_wri = CWriter(ssd, large_font, clock_fg, clock_bg, verbose=False)
info_wri.set_clip(True, True, False)
clock_wri.set_clip(True, True, False)

clock_width = clock_wri.stringlen('00')
clock_height = large_font.height()

info_box = Textbox(info_wri, 170,5,230,6, bdcolor=False)
hours_label = Label(clock_wri, clock_h_y-round(clock_height/2), clock_h_x-round(clock_width/2), clock_width, bdcolor=False, align=2)
mins_label = Label(clock_wri, clock_m_y-round(clock_height/2), clock_m_x-round(clock_width/2), clock_width, bdcolor=False, align=2)

# *** GLOBAL FUNCTIONS ***

def get_light_level():
  light_level = 65535 - light_sensor.read_u16()
  return int(light_level / 655.35)

def set_backlight(percentage):
  backlight_pwm.duty(int(percentage * 10.23))    # 1023 / 100

def msg(m):
  info_box.append(m)
  refresh(ssd)

def startup():
  
  msg("Starting...")
  # Cycle the rear LEDs on startup then turn them off
  green_led.on()
  blue_led.on()
  red_led.on()
  green_led.off()
  time.sleep(0.25)
  green_led.on()
  blue_led.off()
  time.sleep(0.25)
  blue_led.on()
  red_led.off()
  time.sleep(0.25)
  green_led.off()
  blue_led.off()
  time.sleep(0.25)
  red_led.on()
  blue_led.on()
  green_led.on()

def load_config():
  # configure with the following commands in the REPL:
  #
  # >>> import json
  # >>> config={'wifissid':'[ssid]','wifipass':'[pass]'}
  # >>> f = open('config.json', 'w')
  # >>> f.write(json.dumps(config))
  # >>> f.close()
  #

  # Read config

  try:
    f=open("config.json","r")
    config=json.loads(f.read())
    f.close()
    return config
  except:
    msg("Couldn't read config")
    raise RuntimeError("Couldn't read config")

def connect_network():

  # Connect to WiFi
  msg('connecting to WIFI with SSID: ' + config['wifissid'])
  wlan.active(True)
  access_points=wlan.scan()
  ssids=[ap[0].decode('UTF-8') for ap in access_points]
  if config['wifissid'] in ssids:
    msg("WiFi connection " + config['wifissid'] + " is available!")
    wlan.connect(config['wifissid'], config['wifipass'])
    # Wait for connection
    while True:
      if wlan.status() < 0 or wlan.status() >= 3:
        break
      msg('Waiting for connection...')
      time.sleep(1)
    ip, subnet, gateway, dns=wlan.ifconfig()
    msg('...connected! ip=' + ip)
    time.sleep(1)
    msg("Setting time from network...")
    time_not_set = True
    while time_not_set:
      try:
        ntptime.timeout=3
        ntptime.settime()
        msg("... time set successfully!")
        time_not_set=False
        blue_led.on()
      except OSError:
        blue_led.on()
        red_led.off()
        msg("Couldn't set time! Retrying in 5s ...")
        time.sleep(5)
        red_led.on()
  else:
    msg('WiFi connection not found. Offline!')

def clock():

  while True:
    t = time.localtime()
    b = get_light_level()
    if b > 2:
      set_backlight(b)
    else:
      set_backlight(2)
    if b < 50:
      info_box.clear()
    
    # clear clock face
    ssd.rect(0,0,ssd.width,165,screen_bg,True)

    # draw hours face
    ssd.ellipse(clock_h_x,clock_h_y,clock_face_r,clock_face_r,clock_bg,True)
    h_angle=math.radians(t[3]*30-90)
    hx=clock_h_x+round(clock_face_r*math.cos(h_angle))
    hy=clock_h_y+round(clock_face_r*math.sin(h_angle))
    ssd.ellipse(hx,hy,clock_index_r,clock_index_r,clock_bg,True)
    ssd.ellipse(hx,hy,clock_index_inner_r,clock_index_inner_r,clock_fg,True)
    
    # draw minutes face
    ssd.ellipse(clock_m_x,clock_m_y,clock_face_r,clock_face_r,clock_bg,True)
    m_angle=math.radians(t[4]*6-90)
    mx=clock_m_x+round(clock_face_r*math.cos(m_angle))
    my=clock_m_y+round(clock_face_r*math.sin(m_angle))
    ssd.ellipse(mx,my,clock_index_r,clock_index_r,clock_bg,True)
    ssd.ellipse(mx,my,clock_index_inner_r,clock_index_inner_r,clock_fg,True)

    hours_label.value('{:02d}'.format(t[3]))
    mins_label.value('{:02d}'.format(t[4]))
    refresh(ssd)

# *** MAIN PROGRAM **

set_backlight(100)
startup()
config=load_config()
connect_network()
clock()
