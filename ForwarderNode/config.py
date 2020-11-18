""" LoPy LoRaWAN Nano Gateway configuration options """

import machine
import ubinascii

WIFI_MAC = ubinascii.hexlify(machine.unique_id()).upper()
# Set  the Gateway ID to be the first 3 bytes of MAC address + 'FFFE' + last 3 bytes of MAC address
GATEWAY_ID = WIFI_MAC[:6] + "FFFE" + WIFI_MAC[6:12]

TREE_LEVEL = 2 #Set until 15
DEVICE_MODE = 1 #1 only forwarder | 2 only node | 3 forwarder and node

# for EU868
#LORA_FREQUENCY = 868100000
#LORA_GW_DR = "SF7BW125" # DR_5s
#LORA_NODE_DR = 5

# for US915
LORA_FREQUENCY = 903900000
LORA_GW_DR = "SF7BW125" # DR_3
LORA_NODE_DR = 3
