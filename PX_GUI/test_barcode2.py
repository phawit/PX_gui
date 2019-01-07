# while 1:
#     barcode = input("Scan Barcode: ")
#     print('Barcode: ' + str(barcode))
from __future__ import print_function
import sys

# fp = open("/dev/hidraw2", "rb")
fp = open('/dev/input/event14', 'rb')

str_list = []
try:
    while True:
        buffer = fp.read(16)
        for c in buffer:
            if ord(c) > 0:
                print(c, end='')
        print("") 

except KeyboardInterrupt:
    fp.close()