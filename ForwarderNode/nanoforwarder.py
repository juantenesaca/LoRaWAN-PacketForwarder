""" LoPy LoRaWAN Nano Forwarder. Can be used for both EU868 and US915. """

import struct
import errno
import machine
import ubinascii
import ujson
import uos
import usocket
import utime
from network import LoRa
from machine import Timer

class NanoForwarder:

    """
    Nano forwarder class, set up by default for use with TTN, but can be configured
    for any other network supporting the Semtech Packet Forwarder.
    Only required configuration is tree_level and device_mode.
    """

    def __init__(self, id, frequency, datarate, level, mode):
        self.id = id
        self.v_start = 0

        self.frequency = frequency
        self.datarate = datarate

        self.level = level
        self.maxlevel = 0
        self.mode = mode

        self.sf = self._dr_to_sf(self.datarate)
        self.bw = self._dr_to_bw(self.datarate)

        self.app_alarm = None

        self.lora = None
        self.lora_sock = None
        self.lorawan = None
        self.lorawan_sock = None

    def start(self):
        """
        Starts the LoRaWAN nano forwarder.
        """
        self._log('Starting LoRaWAN nano forwarder with id: {}', self.id)

        # Define ID and Keys in LORAWAN mode.
        if self.mode != 1:
            self.lorawan = LoRa(mode=LoRa.LORAWAN)
            self.dev_addr = struct.unpack(">l", ubinascii.unhexlify('2601160C'))[0]  #create an ABP authentication params
            self.nwk_swkey = ubinascii.unhexlify('5864350495E1123A5AD221DF700CCEC8')
            self.app_swkey = ubinascii.unhexlify('4B751B14B6C2C7BAB00B46EEA30E920D')
            for channel in range(0, 72):                                            # remove all the channels
                self.lorawan.remove_channel(channel)
            for channel in range(0, 72):                                            # set all channels to the same frequency (must be before sending the OTAA join request)
                self.lorawan.add_channel(channel, frequency=903900000, dr_min=0, dr_max=3)
            self.lorawan.join(activation=LoRa.ABP, auth=(self.dev_addr, self.nwk_swkey, self.app_swkey)) # join a network using ABP (Activation By Personalization)
            self.lorawan_sock = usocket.socket(usocket.AF_LORA, usocket.SOCK_RAW)   # create a LoRa usocket
            self.lorawan_sock.setsockopt(usocket.SOL_LORA, usocket.SO_DR, 3)        # set the LoRaWAN data rate
            self.lorawan_sock.setblocking(True)                                    # make the usocket blocking

        #Saving LoRaWAN State in NVRAM
        if self.mode == 3:
            self.lorawan.nvram_save()

        # initialize the LoRa radio in LORA mode
        if self.mode != 2:
            self._log('Setting up the LoRa radio at {} Mhz using {}', self._freq_to_float(self.frequency), self.datarate)
            self.lora = LoRa(
                mode=LoRa.LORA,
                frequency=self.frequency,
                bandwidth=self.bw,
                sf=self.sf,
                preamble=8,
                coding_rate=LoRa.CODING_4_5,
                tx_iq=True
            )

            # create a raw LoRa socket
            self.lora_sock = usocket.socket(usocket.AF_LORA, usocket.SOCK_RAW)
            self.lora_sock.setblocking(False)
            self.lora_tx_done = False
            self.lora.callback(trigger=(LoRa.RX_PACKET_EVENT), handler=self._lora_cb)
            #self.lora.callback(trigger=(LoRa.RX_PACKET_EVENT), handler=self._lorawan_cb)

        #initialize application
        if self.mode != 1:
            self.app_alarm = Timer.Alarm(handler=lambda t: self._app(), s=7, periodic=True)
            self._log('LoRaWAN nano forwarder online')

    def stop(self):
        """
        Stops the LoRaWAN nano forwarder.
        """
        self._log('Stopping...')

        # send the LoRa radio to sleep
        self.lora.callback(trigger=None, handler=None)
        self.lora.power_mode(LoRa.SLEEP)

        # cancel all the alarms
        self.app_alarm.cancel()

    def _dr_to_sf(self, dr):
        sf = dr[2:4]
        if sf[1] not in '0123456789':
            sf = sf[:1]
        return int(sf)

    def _dr_to_bw(self, dr):
        bw = dr[-5:]
        if bw == 'BW125':
            return LoRa.BW_125KHZ
        elif bw == 'BW250':
            return LoRa.BW_250KHZ
        else:
            return LoRa.BW_500KHZ

    def _sf_bw_to_dr(self, sf, bw):
        dr = 'SF' + str(sf)
        if bw == LoRa.BW_125KHZ:
            return dr + 'BW125'
        elif bw == LoRa.BW_250KHZ:
            return dr + 'BW250'
        else:
            return dr + 'BW500'

    def _lorawan_cb(self, lora):
        """
        LoRa radio events callback handler.
        """
        events = lora.events()
        if events & LoRa.RX_PACKET_EVENT:
            print('Segundo Recivido')

    def _lora_cb(self, lora):
        """
        LoRa radio events callback handler.
        """
        events = lora.events()
        if events & LoRa.RX_PACKET_EVENT:
            #try:

            #\xa0

            rx_data = self.lora_sock.recv(256)
            if rx_data[0] == 64:
                hop_byte = (self.level - 1)*16 + self.level
                rx_data = struct.pack("B", hop_byte) + rx_data
            else:
                hop_byte = int(rx_data[0]) - 16
                rx_data = struct.pack("B", hop_byte) + rx_data[1:]

            hop_byte = int(hop_byte/16)
            print(hop_byte)
            print(rx_data)
            try:
                if hop_byte == (self.level - 1):
                    self._send_up_link(rx_data)
            except:
                self._log('Failed in Uplink Packet')

            #except:
            #    self._log('Failed in Receive Packet')

    def _freq_to_float(self, frequency):
        """
        MicroPython has some inprecision when doing large float division.
        To counter this, this method first does integer division until we
        reach the decimal breaking point. This doesn't completely elimate
        the issue in all cases, but it does help for a number of commonly
        used frequencies.
        """

        divider = 6
        while divider > 0 and frequency % 10 == 0:
            frequency = frequency // 10
            divider -= 1
        if divider > 0:
            frequency = frequency / (10 ** divider)
        return frequency

    def _app(self):

        if self.mode == 3:
            self.lorawan = LoRa(mode=LoRa.LORAWAN)
            self.lorawan.nvram_restore()

        # Struct your data here
        self.v_start = self.v_start + 1
        trama = struct.pack(">I", self.v_start)

        try:
            self.lorawan_sock.send(trama)
            self._log('Sent: {} #:  {}', trama, self.v_start)
        except:
            self._log('Node Packet Failed')

        if self.mode == 3:
            self.lorawan.nvram_save()
            self.lora = LoRa(
                mode=LoRa.LORA,
                frequency=self.frequency,
                bandwidth=self.bw,
                sf=self.sf,
                preamble=8,
                coding_rate=LoRa.CODING_4_5,
                tx_iq=True
            )

    def _send_up_link(self, data):
        """
        Transmits a uplink message over LoRa.
        """
        self.lora = LoRa(
            mode=LoRa.LORA,
            frequency=self.frequency,
            bandwidth=self.bw,
            sf=self.sf,
            preamble=8,
            coding_rate=LoRa.CODING_4_5,
        )
        self.lora_sock.send(data)
        data = ubinascii.b2a_base64(data)[:-1]
        self._log(
            'Sent uplink packet: {}',
            data
        )

    def _log(self, message, *args):
        """
        Outputs a log message to stdout.
        """

        print('[{:>10.3f}] {}'.format(
            utime.ticks_ms() / 1000,
            str(message).format(*args)
            ))
