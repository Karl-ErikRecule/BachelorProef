from machine import Timer
from network import Sigfox
import socket
import pycom
import time
import ubinascii
from LIS2HH12 import LIS2HH12
import gc
from L76GNSS import L76GNSS
from pytrack import Pytrack
import math
import struct
from ownLib import OwnLib
import binascii

TIME_SLEEP = const(6000) #Instellen van de timer (in seconden)
NUMBER_OF_VIBRATIONS = const(5) #Drempel waarover het aantal cycli moet gaan om te sturen
TRILLINGS_DREMPEL = const(63) #van 62.5 tot 8000mG
DUUR_DREMPEL = const(8000) #van 160 tot 40800ms. Duur van de trilling

# byte 0 is het ID van het toestel, hier op 1 geplaatst.
lijstBytes = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
lib = OwnLib() #instantie aanmaken van de eigen library
lib.preSetup() #de wifi uitschakelen

#methode om de array op te maken die verstuurd moet worden.
def setup_array():
    if(lib.get_number('cycle') != None): #Als de waarde in het geheugen bestaat, deze uitlezen.
        lijstBytes[11] = lib.get_number('cycle') #opvragen van de waarde in het geheugen.
    else:
        lijstBytes[11] = 0
    return bytearray(lijstBytes) #array van bytes teruggeven.

#heartbeat uitschakelen om de led aan te kunnen sturen.
pycom.heartbeat(False)

#instantie aanmaken van de pytrack (voor deepsleep)
#instantie aanmaken van de accelerometer.
py = Pytrack()
acc = LIS2HH12()

# display the reset reason code and the sleep remaining in seconds
# possible values of wakeup reason are:
WAKE_REASON_ACCELEROMETER = 1
WAKE_REASON_PUSH_BUTTON = 2
WAKE_REASON_TIMER = 4
WAKE_REASON_INT_PIN = 8
wakeReason = py.get_wake_reason() #reden van wakeup opvragen

cycliInGeheugen = lib.get_number('cycle')

print(" Cycle: " + '{}'.format(cycliInGeheugen)) #uitprinten van het aantal cycli in het geheugen, voordat er een nieuwe waarde bijgeteld wordt.
print("Wakeup reason: " + str(wakeReason)) #wakeReason weergeven
time.sleep(0.5)

# disable wakeup source from INT pin
py.setup_int_pin_wake_up(False)

# enable activity and also inactivity interrupts, using the default callback handler
py.setup_int_wake_up(True, True)



if (py.get_wake_reason() == WAKE_REASON_ACCELEROMETER): #Wanneer de accellerometer voor wake up zorgt, 1 bijtellen in het geheugen bij cycle
    pycom.rgbled(0x00FF00) #led kleurt groen als een trilling waargenomen is.
    lib.store_number('cycle')
elif(py.get_wake_reason() == WAKE_REASON_PUSH_BUTTON): #Wanneer er op de knop gedrukt wordt zal er gestuurd worden wanneer er data in het geheugen aanwezig is.
    if(lib.get_number('cycle') != 0): #enkel sturen wanneer er data aanwezig is.
        lib.setup_sigfox_and_send(setup_array()) #methode aanroepen die het versturen voor zich neemt, krijgt de array mee die deze moet versturen.
        lib.reset_number('cycle') #resetten van de waarde in het geheugen
elif(py.get_wake_reason() == WAKE_REASON_TIMER): #Wanneer de timer afgelopen is alles doorsturen
    if(lib.get_number('cycle') != 0): #enkel sturen wanneer er data aanwezig is.
        lib.setup_sigfox_and_send(setup_array())
        lib.reset_number('cycle')

if(lib.get_number('cycle') >= NUMBER_OF_VIBRATIONS): #als er meer data in het geheugen aanwezig is dan de thresold: versturen van de data
    lib.setup_sigfox_and_send(setup_array())
    lib.reset_number('cycle')

#instellen van de drempelwaardes voor de accelerometer.
acc.enable_activity_interrupt(TRILLINGS_DREMPEL, DUUR_DREMPEL)

#instellen van de deepsleep (timer instellen)
py.setup_sleep(TIME_SLEEP)
py.go_to_sleep(False) #False om de gps uit te schakelen.
