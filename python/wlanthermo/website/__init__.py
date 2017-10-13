#!/usr/bin/env python3
# coding=utf-8

from flask import render_template, jsonify
import logging
import datetime
import socket
from wlanthermo.version import VERSION
from wlanthermo.settings import Settings
import locale
import uuid

__author__ = 'Björn Schrader <wlanthermo@bjoern-schrader.de>'
__license__ = 'GNU General Public License http://www.gnu.org/licenses/gpl.html'
__copyright__ = 'Copyright (C) 2017 by WLANThermo Project - Released under terms of the GPLv3 License'

class Website():
    def __init__(self, wlanthermo):
        self.wlanthermo = wlanthermo
        self.app = wlanthermo.app
        self.db = wlanthermo.db
        self.logger = logging.getLogger(__name__)

    def register_url(self):
        self.app.add_url_rule('/',
                              view_func=self.index)
        self.app.add_url_rule('/api/system',
                              view_func=self.sysinfo_api)

    def index(self):
        return render_template('index.html')

    def sysinfo(self):
        syssettings = Settings(self.wlanthermo, 'system')
        retval = dict()
        retval['time'] = datetime.datetime.utcnow()
        retval['ap'] = 'TODO'
        retval['host'] = socket.gethostbyaddr(socket.gethostname())[0]
        retval['language'] = syssettings.get('language') or syssettings.set('language', 'de_DE')
        retval['unit'] = syssettings.get('temp_unit') or syssettings.set('temp_unit', 'temp_celsius')
        retval['software_version'] = VERSION
        retval['hardware_version'] = syssettings.get('hardware_version') or syssettings.set('hardware_version', 'v2')
        retval['uuid'] = syssettings.get('uuid') or syssettings.set('uuid', str(uuid.uuid4()))
        retval['update_available'] = False
        return retval

    def sysinfo_api(self):
        return jsonify(self.sysinfo())

