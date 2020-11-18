""" LoPy LoRaWAN Nano Gateway configuration options """

import machine
import ubinascii

WIFI_MAC = ubinascii.hexlify(machine.unique_id()).upper()
# Set  the Gateway ID to be the first 3 bytes of MAC address + 'FFFE' + last 3 bytes of MAC address
GATEWAY_ID = WIFI_MAC[:6] + "FFFE" + WIFI_MAC[6:12]

SERVER = 'router.eu.thethings.network'
PORT = 1700
#SERVER = '190.15.132.17'
#PORT = 1680

NTP = "pool.ntp.org"
NTP_PERIOD_S = 3600

#WIFI_SSID = 'Ofi_ATIMC'
#WIFI_PASS = 'diucucuenca'
#WIFI_SSID = 'FAST'
#WIFI_PASS = '1234asdf'
WIFI_SSID = 'CRUC'
WIFI_PASS = 'cruc2016-7'
#WIFI_SSID = 'SandrySarmiento'
#WIFI_PASS = '0101990190S'

# for EU868
#LORA_FREQUENCY = 868100000
#LORA_GW_DR = "SF7BW125" # DR_5s
#LORA_NODE_DR = 5

# for US915
LORA_FREQUENCY = 903900000
LORA_GW_DR = "SF7BW125" # DR_3
LORA_NODE_DR = 3
