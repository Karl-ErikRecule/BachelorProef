from machine import Timer
from network import Sigfox
from network import WLAN
from network import LTE
from network import Bluetooth
import pycom
import time
import socket
import ubinascii
from LIS2HH12 import LIS2HH12
import gc
from L76GNSS import L76GNSS
from pytrack import Pytrack
import math
import struct
import binascii


class OwnLib:

# Uitschakelen van de overbodige functionaliteiten. Gps wordt uitgeschakeld bij het initialiseren van de deep sleep.
    def preSetup(self):
        wlan = WLAN()
        wlan.deinit() #Wlan uitschakelen
        # Uitschakelen van LTE en Bluetooth zorgt voor een grote vertraging. Normaal zijn deze niet actief dus moeten ze niet uitgeschakeld worden.
        # lte = LTE()
        # lte.deinit(reset=True) #lte (4G) uitschakelen

        # ble = Bluetooth()
        # ble.deinit() #Disable Bluetooth
        print("preSetup completed")

    #return true wanneer voltooid
    def setup_sigfox_and_send(self, lijstBytes):
        pycom.heartbeat(False)
        # init Sigfox for RCZ1 (Europe)
        sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ1)
        pycom.rgbled(0xf4eb42) # geel

        # create a Sigfox socket
        s = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
        pycom.rgbled(0x00007f) # blauw

        # make the socket blocking
        s.setblocking(True)
        pycom.rgbled(0x9242f4) # paars

        # configure it as uplink only
        s.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, True)
        pycom.rgbled(0xffffff) # wit
        print("Door de setup gelopen, bezig met verzenden...")
    #Hieronder wijzigingen
        verstuurd = False
        if(len(lijstBytes) > 12): #controleren als de lengte niet meer is dan 12 bytes
            error = "Maximum aantal bytes overschreden. Maximum is 12 bytes, er zijn %d bytes proberen te verzenden." % (len(lijstBytes))
            print(error)
            raise ValueError(error)
            verstuurd = False
        else:
            try:
                verstuurd = s.send(lijstBytes) #Bytes sturen
                time.sleep(2) #Even wachten omdat het programma anders vastloopt. Er wordt dan meteen overgegaan naar de volgende regel code, terwijl de data nog niet verstuurd is.
                antwoord = s.recv(32) #Wachten op downlink message
                print("Verstuurd: " + '{}'.format(verstuurd) + " antwoord: " + '{}'.format(binascii.hexlify(antwoord)))
                print("VERZONDEN & DOWNLINK OK")
            except OSError as e: #Error opvangen
                if e.args[0] == 100:
                    print("Probleem met OSError: [Errno 100] ENETDOWN")
                    print("VERZONDEN, DOWNLINK NIET OK")
            verstuurd = True
        s.close() #Sluiten van de socket.
        return (verstuurd)

#Opslaan van een werkcycli in NVRAM, zodat na deepsleep de waarde niet verloren gaat
# Men kan verschillende keys meegeven om verschillende waardes bij te houden. Het opvragen van de waarde in het geheugen gebeurt aan de hand van de keys.
    def store_number(self, key):
        i = pycom.nvs_get(key)
        if i is not None: #als de key al bestaat
            pycom.nvs_set(key, i+1)
        else: #aanmaken van de key als deze nog niet bestaat.
            pycom.nvs_set(key, 1)

#Resetten van een waarde. Eigenlijk niet resetten maar op 0 plaatsen, anders problemen bij het opvragen wanneer de waarde None is.
    def reset_number(self, key):
        pycom.nvs_set(key, 0)

# Geeft de waarde terug onder een bepaalde key
    def get_number(self, key):
        if(pycom.nvs_get(key) != None):
            return (pycom.nvs_get(key))
        else:
            return 0
