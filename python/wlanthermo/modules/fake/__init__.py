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


from requests import post, get, put
import logging
from random import uniform
import datetime
import time

__author__ = 'Björn Schrader <wlanthermo@bjoern-schrader.de>'
__license__ = 'GNU General Public License http://www.gnu.org/licenses/gpl.html'
__copyright__ = 'Copyright (C) 2017 by WLANThermo Project - Released under terms of the GPLv3 License'

API_URL = 'http://localhost:5000'

def run_fake_module(startapp, stopapp):
    fake_module = FakeModule(startapp, stopapp)
    fake_module.run()

class FakeModule:
    def __init__(self, startapp, runapp):
        self.logger = logging.getLogger(__name__)
        self.module_id = post(API_URL + '/api/modules', data={'name': __name__, 'sensor_types': ['ntc_old', 'rtd_pt']}).json()
        self.startapp = startapp
        self.runapp = runapp
        for channel in range(8):
            post('{api_url}/api/channels/{module_id}/{channel_id}'.format(
                api_url=API_URL,
                module_id=self.module_id,
                channel_id=channel + 1
            ), data={'unit': 'temp_celsius'}).json()
        self.channels = [0 for i in range(8)]


    def run(self):
        self.startapp.wait()
        while self.runapp:
            timestamp = datetime.datetime.utcnow()
            for channel, channel_value in enumerate(self.channels):
                channel_value += uniform(-5.0, 5.0)
                if channel_value > 300:
                    channel_value = 300.0
                elif channel_value < -30:
                    channel_value = -30.0
                put('{api_url}/api/channels/{module_id}/{channel_id}'.format(
                    api_url=API_URL,
                    module_id=self.module_id,
                    channel_id=channel + 1
                ), data={'value': channel_value, 'timestamp': timestamp}).json()
            time.sleep(3)
