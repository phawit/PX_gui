#!/usr/bin/env python

from evdev import InputDevice, ecodes, list_devices
from select import select

keys = "X^1234567890XXXXqwertzuiopXXXXasdfghjklXXXXXyxcvbnmXXXXXXXXXXXXXXXXXXXXXXX"
dev = InputDevice("/dev/input/event14")

barcode = ""
while True:
    r,w,x = select([dev], [], [])

    for event in dev.read():
        if event.type == 1 and event.value == 1:
             barcode += (keys[event.code])
    if (len (barcode)) > 13:
        break
        
print("Barcode:" + barcode[:-1])