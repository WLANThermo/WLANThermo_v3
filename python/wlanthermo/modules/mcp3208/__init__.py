#!/usr/bin/python3
# coding=utf-8

# Copyright (c) 2013, 2014, 2015 Armin Thinnes
# Copyright (c) 2015, 2016, 2017 Björn Schrader
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import math
from struct import pack, unpack
from wlanthermo.modules import *
from multiprocessing import Process, Lock, Event
import logging
import time
import json

__author__ = 'Björn Schrader <wlanthermo@bjoern-schrader.de>'
__license__ = 'GNU General Public License http://www.gnu.org/licenses/gpl.html'
__copyright__ = 'Copyright (C) 2017 by WLANThermo Project - Released under terms of the GPLv3 License'

class Mcp3208:
    def __init__(self, module_id=1):
        self.module_id = module_id
        self.channel_count = 8
        self.channels = range(self.channel_count)

        self.spidev = None
        self.pi = None
        self.adc_steps = 4096
        self.adc_maxvalue = self.adc_steps - 1

        self.config = {
            'spi_SCLK': 18,
            'spi_MOSI': 24,
            'spi_MISO': 23,
            'spi_CS': 25,
            'border': 15,
            'spi_mode': 'spidev',
            'hardware_version': 'v2',
            'ref_voltage': 3.3,
            'sample_count': 100,
            'r_measurement': [
                47000, 47000, 47000, 47000,
                47000, 47000, 47000, 47000,
            ],
            'interval': 3,
        }

        self.logger = logging.getLogger(__name__)
        # Upper and lower limtit to filter out open circuit and short circuit
        
        

        self.sensors = [
            {'type': None}, {'type': None}, {'type': None}, {'type': None},
            {'type': None}, {'type': None}, {'type': None}, {'type': None},
        ]

    def init_spi(self):
        """
        Initializes the SPI port 
        """
        if self.config['spi_mode'] == 'pigpiod':
            self.logger.info('Initialized in pigpiod mode')
            import pigpio
            self.pi = pigpio.pi()
            try:
                retval = self.pi.bb_spi_open(
                    self.config['spi_CS'],
                    self.config['spi_MISO'],
                    self.config['spi_MOSI'],
                    self.config['spi_SCLK'],
                    250000,
                    0
                )
            except pigpio.error as e:
                if str(e) == "'GPIO already in use'":
                    retval = 0
                else:
                    raise

        elif self.config['spi_mode'] == 'spidev':
            self.logger.info('Initialized in spidev mode')
            import spidev
            self.spidev = spidev.SpiDev()
            self.spidev.open(32766, 0)

    def get_adc(self, channel):
        """
        Gets the ADC value from an specified ADC channel 
        """
        if channel > 7:
            raise ValueError()
        if self.config['spi_mode'] == 'pigpiod':
            command = pack('>Hx', (0x18 + channel) << 6)
            return unpack('>xH', self.pi.bb_spi_xfer(self.config['spi_CS'], command)[1])[0] & 0x0fff
        elif self.config['spi_mode'] == 'spidev':
            # B0: Start byte, single channel + msb from channel
            # B1: 2 lsb from channel
            # B2: fill byte for transfer
            command = [0x06 | ((channel & 0x04) >> 2), (channel & 0x03) << 6, 0x00]
            return bytearray_to_int(bytearray(self.spidev.xfer(command))) & 0x0fff

    def get_voltage(self, adc):
        """
        Calculates the voltage measured by an ADC port
        """
        return adc * self.config['ref_voltage'] / self.config['adc_steps']

    def get_resistance(self, adc, r_measurement):
        """
        Calculates the resistance measured by an ADC port
        """
        if not self.config['hardware_version'] == 'v1':
            adc = self.config['adc_steps'] - 1 - adc

        r_sensor = r_measurement * ((self.config['adc_steps'] / adc) - 1)
        return r_sensor


    def get_sensortypes(self):
        types = [func[5:] for func in dir(self) if callable(getattr(self, func)) and func.startswith("calc_")]
        return types

    ###
    # calc_* functions are automatically used by sensor_type definition, so
    # def calc_XXX(self, adc, r_measurement, sensor_conf):
    # has always to be used in the definition of such functions!
    ###

    def calc_voltage(self, adc, r_measurement, sensor_conf):
        """
        Calculates the voltage measured by an ADC channel
        """
        return self.get_voltage(adc)

    def calc_resistance(self, adc, r_measurement, sensor_conf):
        """
        Calculates the resistance measured by an ADC channel
        """
        return self.get_resistance(adc, r_measurement)

    def calc_ntc(self, adc, r_measurement, sensor_conf):
        """
        Calculates the temperature measured by an NTC connected to an ADC channel
        """

        r_sensor = self.get_resistance(adc, r_measurement)

        try:
            v = math.log(r_sensor / sensor_conf.r_nominative)
            temp = (
                       1 /
                       (
                           sensor_conf.coeff_a +
                           sensor_conf.coeff_b * v +
                           sensor_conf.coeff_c * v ** 2 +
                           sensor_conf.coeff_d * v ** 3
                       )
                   ) - 273.15
        except:
            raise TempCalcError('Error while calculating temperature')

        return temp

    def calc_ntc_old(self, adc, r_measurement, sensor_conf):
        """
        Calculates the temperature measured by an NTC connected to an ADC channel
         - uses old WLANThermo calculation formula
        """

        r_sensor = self.get_resistance(adc, r_measurement)

        try:
            v = math.log(r_sensor / sensor_conf.r_nominative)
            temp = (
                       1 /
                       (
                           sensor_conf.coeff_a +
                           sensor_conf.coeff_b * v +
                           sensor_conf.coeff_c * v ** 2
                       )
                   ) - 273.0
        except:
            raise TempCalcError('Error while calculating temperature')

        return temp

    def calc_rtd_pt(self, adc, r_measurement, sensor_conf):
        """
        Calculates the temperature measured by an pt type RTD connected to an ADC channel
        """
        r_sensor = self.get_resistance(adc, r_measurement)

        coeff_a = 3.9083E-3
        coeff_b = -5.7750E-7

        try:
            temp = -1 * math.sqrt(
                r_sensor / (sensor_conf.r_nominative * coeff_b) +
                coeff_a ** 2 / (4 * coeff_b ** 2) - 1 / coeff_b
            ) - coeff_a / (2 * coeff_b)
        except:
            raise TempCalcError('Error while calculating temperature')

        return temp

    def calc_poly_u(self, adc, r_measurement, sensor_conf):
        """
        Calculates the result measured by a voltage connected to an ADC channel
        """
        u = self.get_voltage(adc)
        result = (
            sensor_conf.coeff_a +
            sensor_conf.coeff_b * u +
            sensor_conf.coeff_c * u ** 2 +
            sensor_conf.coeff_d * u ** 3 +
            sensor_conf.coeff_e * u ** 4
        )
        return result

    def calc_poly_r(self, adc, r_measurement, sensor_conf):
        """
        Calculates the result measured by a resistance connected to an ADC channel
        """
        r = self.get_resistance(adc, r_measurement)
        result = (
            sensor_conf.coeff_a +
            sensor_conf.coeff_b * r +
            sensor_conf.coeff_c * r ** 2 +
            sensor_conf.coeff_d * r ** 3 +
            sensor_conf.coeff_e * r ** 4
        )
        return result

    def median_filter(self, samples):
        """
        Implements an averaging median filter
        Window size is 1 + ln(len(samples))
        """
        length = len(samples)
        sorted_samples = sorted(samples)

        index = int(round(length * 0.5))

        area_groesse = 1 + int(round(math.log(length)))
        window_samples = sorted_samples[index - area_groesse:index + area_groesse + 1]

        return sum(window_samples) / len(window_samples)

    def sample_all(self):
        """
        Samples all channels defined in self.channels
        """
        self.logger.info('Sampling all channels')
        samples = [[] for channel in self.channels]

        # Sample all channels
        for sample in range(self.config['sample_count']):
            for channnel in self.channels:
                samples[channnel].append(self.get_adc(channnel))

        # Calculate resulting median values
        results = []

        for channel in self.channels:
            sensor_conf = self.sensors[channel]
            r_measurement = self.config['r_measurement'][channel]

            result_state = ResultState.NONE
            result_value = None
            result_unit = None

            if sensor_conf['type'] is None:
                result_state = ResultState.ERR_NOSENSOR
            else:
                median_value = self.median_filter(samples[channel])
                # Calculate sensor results
                if sensor_conf['type'] in ('ntc', 'rtd_pt'):
                    # Check for upper and lower limits
                    if median_value < self.config['border']:
                        result_state = ResultState.ERR_LO
                    elif median_value > self.adc_maxvalue - self.config['border']:
                        result_state = ResultState.ERR_HI
                    else:
                        # Calculate results
                        try:
                            calc_function = getattr(self, 'calc_' + str(sensor_conf['type']))
                            result_value = calc_function(median_value, r_measurement, sensor_conf)
                            result_state = ResultState.OK
                            result_unit = sensor_conf['unit']
                        except TempCalcError:
                            result_state = ResultState.ERR
                            self.logger.error(
                                'Calculating result failed for channel: {channel}'.format(channel=channel))
                        except AttributeError:
                            result_state = ResultState.ERR
                            self.logger.error(
                                'Sensor type {sensor_type} is unknown for channel: {channel}'.format(
                                    sensor_type=sensor_conf['type'],
                                    channel=channel))
                else:
                    result_state = ResultState.ERR_NOSUPPT

                self.logger.debug('Channel {channel}: state {state}, value: {value} {unit}, raw: {raw}'.format(
                    state=result_state.name,
                    channel=channel,
                    value=result_value,
                    unit=result_unit,
                    raw=median_value,
                    ))

            result = ChannelResult(
                module=self.module_id,
                channel=channel,
                state=result_state,
                value=result_value,
                unit=result_unit,
            )
            results.append(result)
        return results

class Mcp3208Process():
    def __init__(self, module_id = 0):
        self.logger = logging.getLogger(__name__)
        self.channel_count = 8

        self.stop = False

        self.module_id = module_id
        self.mcp3208 = Mcp3208(module_id)

    def start(self):
        self.register_module()
        self.register_channels()

    def run(self):
        self.mqtt_client.connect("iot.eclipse.org", 1883, 60)

        self.mqtt_client.loop_start()

        # Main loop
        self.wait_on_config()
        self.loop()

        self.mqtt_client.loop_stop(force=False)

    def terminate(self):
        self.stop = True

    def register_module(self):
        pass

    def loop(self):
        while not self.stop:
            start_time = time.time()
            with self.config_mcp3208_lock:
                for result in self.mcp3208.sample_all():
                    self.mqtt_client.publish('set/channel/{module_id}/{channel_id}/'.format(
                        module_id=result.module,
                        channel_id=result.channel
                    ), payload=json.dumps(result), qos=0, retain=False)
            with self.config_mcp3208_lock:
                loop_wait = self.mcp3208.config['interval'] - (time.time() - start_time)
            time.sleep(loop_wait)

    def wait_on_config(self):
        self.config_sensors_received.wait()
        self.config_channels_received.wait()
        self.config_mcp3208_received.wait()

    def update_sensors(self):
        with self.config_sensors_lock:
            for channel in count(self.mcp3208.channel_count()):
                with self.config_mcp3208_lock:
                    self.mcp3208.sensors[channel] = self.sensors[self.channels[channel]['sensor_type']].copy()
        
    def on_mqtt_connect(self, client, userdata, flags, rc):
        self.logger.info('Connected with result code ' + str(rc))
        
        client.subscribe("sensor_config/")
        client.subscribe("config/mcp3208/")
        client.subscribe("command/")
        if self.config_sensors_received.is_set()
            # In case of lost connection resubscribe
            client.subscribe("channel_config/{module_id}/+/".format(module_id=self.module_id))

    def on_mqtt_message(self, client, userdata, msg):
        self.logger.warning('No callback for topic "{topic}" defined.'.format(topic=msg.topic))

    def on_config_mcp3208(self, client, userdata, msg):
        self.logger.info('Config config_mcp3208 received')
        with self.config_mcp3208_lock:
            self.mcp3208.config.update(json.loads(msg.payload))
        self.config_mcp3208_received.set()

    def on_config_sensors(self, client, userdata, msg):
        self.logger.info('Config config_sensors received')
        with self.config_sensors_lock:
            self.sensors.update(json.loads(msg.payload))
        if not self.config_sensors_received.is_set()
            self.logger.info('Config config_sensors for the first time received, subscribing to channel_config')
            self.config_sensors_received.set()
            client.subscribe("channel_config/{module_id}/+/".format(module_id=self.module_id))
        if self.config_channels_received.is_set():
            self.update_sensors()

    def on_config_channels(self, client, userdata, msg):
        self.logger.info('Config config_channels received')
        
        message = json.loads(msg.payload)
        
        if message['module_id'] == self.module_id:
            # Save channel config
            with self.config_channels_lock:
                self.channels[message['channel_id']].update(message)
            # Update sensor config
            with self.config_mcp3208_lock:
                self.mcp3208.sensors[message['channel_id']] = self.sensors[message['sensor_type']].copy()
        
        if not None in self.mcp3208.sensors:
            # All sensors have been set
            if not self.config_channels_received.is_set()
                self.logger.info('Received all required config_channels!')
                self.config_channels_received.set()

    def on_command(self, client, userdata, msg):
        command = msg.payload
        self.logger.info('Command "{command}" received'.format(command=command))
        if command in ('shutdown', 'restart'):
            self.terminate()

