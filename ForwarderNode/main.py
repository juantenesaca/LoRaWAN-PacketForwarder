""" LoPy LoRaWAN Nano Gateway example usage """

import config
from nanoforwarder import NanoForwarder

if __name__ == '__main__':
    nanofw = NanoForwarder(
        id=config.GATEWAY_ID,
        frequency=config.LORA_FREQUENCY,
        datarate=config.LORA_GW_DR,
        level=config.TREE_LEVEL,
        mode=config.DEVICE_MODE
        )

    nanofw.start()
    nanofw._log('You may now press ENTER to enter the REPL')
    input()
