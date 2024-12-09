import board
import digitalio
import displayio
import time
import random
import neopixel

from adafruit_display_text import label
import adafruit_imageload
import terminalio
from adafruit_display_shapes.rect import Rect

import keypad

'''
    Creates the image data for each image
'''
    
#setup keypad events
k = keypad.ShiftRegisterKeys(
    clock=board.BUTTON_CLOCK,
    data=board.BUTTON_OUT,
    latch=board.BUTTON_LATCH,
    key_count=8,
    value_when_pressed=True,
)

#setup neopixel strand for timer
GREEN = (0, 255, 0)
YELLOW = (255, 100, 0)
ORANGE = (200, 150, 0)
PINK = (100, 0, 100)
RED = (255, 0, 0)

class PixelManager(object):
    def __init__(self):
        self.level = 0
        self.pixels = neopixel.NeoPixel(board.NEOPIXEL, 5, brightness=0.02, auto_write=False)
        self.show_level(self.level)
        
    def clear(self):
        for i in range(5):
            self.pixels[i] = (0,0,0)
            
        self.pixels.show()
        
    def show_level_up(self):
        self.level = self.level + 1
        for i in range(5):
            self.show_level(i)
            time.sleep(0.5)
            
        self.show_level(self.level)
        time.sleep(1)
        
    def show_win(self):
        self.pixels.brightness = 0.2
        self.clear()
        while(True):
            for i in range(5):
                self.show_level(i)
                time.sleep(0.1)
        
    def show_level(self, level):
        self.clear()
        if level == 0:
            self.pixels[0] = RED
        if level == 1:
            self.pixels[0] = RED
            self.pixels[1] = PINK
        if level == 2:
            self.pixels[0] = RED
            self.pixels[1] = PINK
            self.pixels[2] = ORANGE
        if level == 3:
            self.pixels[0] = RED
            self.pixels[1] = PINK
            self.pixels[2] = ORANGE
            self.pixels[3] = YELLOW
        if level == 4:
            self.pixels[0] = RED
            self.pixels[1] = PINK
            self.pixels[2] = ORANGE
            self.pixels[3] = YELLOW
            self.pixels[4] = GREEN
            
        self.pixels.show()


class PulseArray(object):
    def __init__(self):
        self.MAXLEN = 6
        self.arr = list()
        self.len = 0

    def add(self, sampletime):
        if len(self.arr) < self.MAXLEN:
            self.arr.append(sampletime)
            self.len += 1

            print(self.arr)
        else:
            return

    def clear_arr(self):
        self.arr = list()
        self.len = 0

    def get_arr(self):
        return self.arr[::]


MAX_PULSE = 1.0
MIN_PULSE = 0.1

class PulseTranslator(object):
    def __init__(self):
        self.pulsearr = PulseArray()
        self.pulsetempo = 0.5

    def add(self, sampletime):
        self.pulsearr.add(sampletime)

    def clear_arr(self):
        self.pulsearr.clear_arr()

    def encode_pulses(self):
        plist = list()
        if self.pulsearr.len == 0:
            print("no items to encode")
            return

        for item in self.pulsearr.get_arr():
            if item <= self.pulsetempo:
                plist.append(0)
            elif item >= self.pulsetempo*2:
                plist.append(1)
            else:
                print("pulse in weird length")
                print("period: %f" % self.pulsetempo)
                print("pulse measured: %f" % item)

        print(plist)
        self.pulsearr.clear_arr()


    def track_period(self, period):
        #if the period is too long for morse code
        print("period: %f" % period)
        if period > 2.5:
            return

        #print("diffperiod: %f" %(period - self.pulsetempo))

        self.pulsetempo = self.pulsetempo + 0.05*(period- self.pulsetempo)
        if self.pulsetempo > 2.5:
            self.pulsetempo = 2.5
        elif self.pulsetempo < 0.1:
            self.pulsetempo = 0.1

        #print("pulsetempo: %f" % self.pulsetempo)

    def get_pulsetempo(self):
        return self.pulsetempo
        
now = 0
class TimerMonitor(object):
    def __init__(self, timeout, cb_function):
        self.base = time.monotonic()
        self.now = time.monotonic()
        self.timeout = timeout
        self.docallback = cb_function

    def check_time(self):
        self.now = time.monotonic()

        if self.now - self.base > self.timeout:
            print("check time")
            self.docallback()
            self.reset_base()

    def set_timeout(self, timeout):
        self.timeout = timeout

    def reset_base(self):
        self.base = time.monotonic()

pulsetranslator = PulseTranslator()
tm = TimerMonitor(1.0, pulsetranslator.encode_pulses)
oldpulse = 0.0
newpulse = 0.0
button_pressed = False #needed to prevent timeout from firing too early

#main while
while True:
    event = k.events.get()
    if event:
        if event.pressed == True or event.released == True:
            if event.key_number == 4: #right
                if event.released == False:
                    print("press")
                    button_pressed = True
                    now = time.monotonic()
                    oldpulse = newpulse
                    newpulse = time.monotonic()
                    pulsetranslator.track_period((newpulse-oldpulse))

                else:
                    print("release")
                    button_pressed = False
                    oldnow = now
                    now = time.monotonic()
                    pulsetranslator.add(now-oldnow)
                    tm.set_timeout(pulsetranslator.get_pulsetempo()*3)

                    tm.reset_base()

            if event.key_number == 5: #up
                pass
            if event.key_number == 6: #down
                pass
            if event.key_number == 7: #left
                print("left")

    #get time calculation
    if button_pressed == False:
        tm.check_time()
