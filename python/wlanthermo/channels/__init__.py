#!/usr/bin/env python3
# coding=utf-8

from collections import namedtuple
from wlanthermo.database.tables import *
from wlanthermo.settings import *
import json
import time
import logging
import datetime
import webcolors
from enum import IntEnum
from threading import Thread
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Float, Boolean
from sqlalchemy.orm import relationship
from flask import jsonify, request, abort

__author__ = 'Björn Schrader <wlanthermo@bjoern-schrader.de>'
__license__ = 'GNU General Public License http://www.gnu.org/licenses/gpl.html'
__copyright__ = 'Copyright (C) 2017 by WLANThermo Project - Released under terms of the GPLv3 License'

PreferredColorList = ['Blue', 'Chartreuse', 'Aquamarine', 'Yellow', 'HotPink', 'Red', 'Purple', 'Green', 'Orange',
                      'Black', 'White', 'Brown', 'Plum', 'SkyBlue', 'OrangeRed', 'Salmon', 'DarkGrey', 'Violet',
                      'Turquoise', 'Khaki', 'DarkViolet', 'SeaGreen', 'SteelBlue', 'Gold', 'DarkGreen', 'MidnightBlue',
                      'DarkKhaki', 'DarkOliveGreen', 'Pink', 'Grey', 'SlateGrey', 'Olive', 'Magenta', 'MediumPurple']


class Channels():
    def __init__(self, wlanthermo):
        self.app = wlanthermo.app
        self.db = wlanthermo.db
        self.logger = logging.getLogger(__name__)
        self.channels = dict()

    def register_api(self):
        self.app.add_url_rule('/api/colors',
                              view_func=self.get_colors_api)
        self.app.add_url_rule('/api/channels/<int:module_id>/<int:channel_id>',
                              methods=['POST'],
                              view_func=self.register_channel_api)
        self.app.add_url_rule('/api/channels/<int:module_id>/<int:channel_id>',
                              view_func=self.get_channels_api)
        self.app.add_url_rule('/api/channels/<int:module_id>',
                              view_func=self.get_channels_api)
        self.app.add_url_rule('/api/channels',
                              view_func=self.get_channels_api)
        self.app.add_url_rule('/api/channels/<int:module_id>/<int:channel_id>',
                              methods=['PUT'],
                              view_func=self.set_channels_api)
        self.app.add_url_rule('/api/channel_config/<int:module_id>/<int:channel_id>',
                              view_func=self.get_channel_config_api)
        self.app.add_url_rule('/api/channel_config/<int:module_id>',
                              view_func=self.get_channel_config_api)
        self.app.add_url_rule('/api/channel_config',
                              view_func=self.get_channel_config_api)
        self.app.add_url_rule('/api/channel_config/<int:module_id>/<int:channel_id>',
                              methods=['POST'],
                              view_func=self.set_channel_config_api)
        self.app.add_url_rule('/api/channel_config/<int:module_id>',
                              methods=['POST'],
                              view_func=self.set_channel_config_api)
        self.app.add_url_rule('/api/channel_config',
                              methods=['POST'],
                              view_func=self.set_channel_config_api)


    def unregister(self, channels_id):
        self.logger.info('Unregistering channel with channel_config id {channels_id}'.format(
            channels_id=channels_id))
        
        channel = ChannelsTable.query.get(channels_id)
        if channel is not None:
            self.db.session.delete(channel)
            self.db.session.commit()
            return True
        else:
            return False
        
    def get_channels(self, module_id=None, channel_id=None):
        query = self.db.session.query(ChannelConfigTable, ChannelsTable).filter(
            ChannelConfigTable.id == ChannelsTable.config_id)
        
        if channel_id is not None:
            query.filter(ChannelConfigTable.channel_id == channel_id)
        if module_id is not None:
            query.filter(ChannelConfigTable.module_id == module_id)
        db_result = query.order_by(ChannelConfigTable.module_id).order_by(ChannelConfigTable.channel_id).all()
        
        result = dict()
        for channel_config, channel in db_result:
            if channel_config.module_id not in result:
                result[channel_config.module_id] = dict()
            result[channel_config.module_id][channel_config.channel_id] = {
                'type': channel_config.type,
                'module_id': channel_config.module_id,
                'channel_id': channel_config.channel_id,
                'name': channel_config.name,
                'unit': channel_config.unit,
                'sensor_type': channel_config.sensor_type,
                'alert_low_limit': channel_config.alert_low_limit,
                'alert_high_limit': channel_config.alert_high_limit,
                'alert_low_enabled': channel_config.alert_low_enabled,
                'alert_high_enabled': channel_config.alert_high_enabled,
                'color': channel_config.color,
                'description': channel_config.description,
                'value': channel.value,
                'timestamp': channel.timestamp,
                'alert_state': channel.alert_state,
                'alert_ack': channel.alert_ack,
            }
        
        if channel_id is not None and module_id is not None:
            try:
                return result[module_id][channel_id]
            except KeyError:
                return None
        elif channel_id is None and module_id is not None:
            try:
                return result[module_id]
            except KeyError:
                return None
        elif channel_id is None and module_id is None:
            return result
        else:
            self.logger.error('Irregular Filter in get_channels')
            return None
        
    def set_channel_config(self, config, module_id=None, channel_id=None):
        # Put into right structure
        if channel_id is not None:
            config = {channel_id: config}
        if module_id is not None:
            config = {module_id: config}
        
        updated_channel_list = []
        
        # Set configuration to database
        for module_id, module_level_config in config.items():
            for channel_id, channel_config in module_level_config.items():
                channel_config_db = self.db.session.query(ChannelConfigTable) \
                    .filter(ChannelConfigTable.module_id == module_id) \
                    .filter(ChannelConfigTable.channel_id == channel_id) \
                    .first()
                updated = False
                for key, value in channel_config:
                    if key not in ('module_id', 'channel_id', 'id'):
                        try:
                            setattr(channel_config_db, key, value)
                            self.logger.debug('Set key {key} to {value}'.format(key=key, value=value))
                            updated = True
                        except AttributeError:
                            self.logger.warning('Key {key} not in channel_config'.format(key=key))
                    else:
                        self.logger.debug('Key {key} not to be set!'.format(key=key))
                if updated:
                    updated_channel_list.append((module_id, channel_id))
        
        self.db.session.commit()
        
        for module_id, channel_id in updated_channel_list:
            self.process(module_id, channel_id, reprocess=True)
        
    def get_channel_config(self, module_id=None, channel_id=None):
        query = self.db.session.query(ChannelConfigTable)
        
        if channel_id is not None:
            query.filter(ChannelConfigTable.channel_id == channel_id)
        if module_id is not None:
            query.filter(ChannelConfigTable.module_id == module_id)
        
        db_result = query.order_by(ChannelConfigTable.module_id).order_by(ChannelConfigTable.channel_id).all()
        
        result = dict()
        for channel_config in db_result:
            if channel_config.module_id not in result:
                result[channel_config.module_id] = dict()
            result[channel_config.module_id][channel_config.channel_id] = {
                'type': channel_config.type,
                'module_id': channel_config.module_id,
                'channel_id': channel_config.channel_id,
                'name': channel_config.name,
                'unit': channel_config.unit,
                'sensor_type': channel_config.sensor_type,
                'alert_low_limit': channel_config.alert_low_limit,
                'alert_high_limit': channel_config.alert_high_limit,
                'alert_low_enabled': channel_config.alert_low_enabled,
                'alert_high_enabled': channel_config.alert_high_enabled,
                'color': channel_config.color,
                'description': channel_config.description,
            }
        
        if channel_id is not None and module_id is not None:
            try:
                return result[module_id][channel_id]
            except KeyError:
                abort(404)
        elif channel_id is None and module_id is not None:
            try:
                return result[module_id]
            except KeyError:
                abort(404)
        elif channel_id is None and module_id is None:
            return result
        else:
            self.logger.error('Irregular Filter in get_channel_config')
            return result
        
    def get_channel_color(self):
        for color in PreferredColorList:
            color_hex = webcolors.name_to_hex(color)
            if self.db.session.query(ChannelConfigTable).filter_by(color=color_hex).first() is None:
                self.logger.info('Color {color} not in use yet.'.format(color=color))
                return color_hex
        else:
            self.logger.error('No free color found')
            return '#000000'
        
    def register(self, module_id, channel_id, unit):
        self.logger.info('Registering module {module_id}, channel {channel_id} with type {unit}'.format(
            module_id=module_id,
            channel_id=channel_id,
            unit=unit))
        
        channel_config = self.db.session.query(ChannelConfigTable).filter_by(module_id=module_id, channel_id=channel_id).one_or_none()
        if channel_config is None:
            self.logger.debug('Adding channel: Module {module_id}, channel {channel_id} to channel config'.format(
                module_id=module_id,
                channel_id=channel_id))
            channel_config = ChannelConfigTable(
                type=ChannelType.channel_data,
                module_id=module_id,
                channel_id=channel_id,
                unit=unit,
                name="Module {module}, channel {channel}".format(module=module_id, channel=channel_id),
                color=self.get_channel_color(),
            )
            self.db.session.add(channel_config)
            self.db.session.commit()
        elif channel_config.unit != unit:
            self.logger.debug('Changing channel: Module {module_id}, channel {channel_id} unit'.format(
                module_id=module_id,
                channel_id=channel_id))
            channel_config.unit = unit
            self.db.session.commit()
        
        channel = self.db.session.query(ChannelsTable).filter_by(config_id=channel_config.id).one_or_none()
        if channel is not None:
            # Clear channel values
            channel.value = None
            channel.alert_state = AlertState.none
            channel.timestamp = datetime.datetime.utcnow()
        else:
            # Add channel
            channel = ChannelsTable(
                config_id=channel_config.id,
                )
            self.db.session.add(channel)
        
        self.db.session.commit()
        
        return channel_config.id

    def process(self, module_id, channel_id, value=None, timestamp=None, reprocess=False):
        channel_config = self.db.session.query(ChannelConfigTable).filter_by(module_id=module_id, channel_id=channel_id).one()
        channel = self.db.session.query(ChannelsTable).filter_by(config_id=channel_config.id).one()

        self.logger.debug('Processing value: {value} for module {module_id}, channel {channel_id}'.format(
            value=value,
            module_id=module_id,
            channel_id=channel_id
        ))

        old_alert_state = channel.alert_state
        if not reprocess:
            channel.value = value
            if timestamp is not None:
                channel.timestamp = timestamp

        if channel.value is None:
            channel.alert_state = AlertState.none
        elif channel.value > channel_config.alert_high_limit and channel_config.alert_high_enabled:
            channel.alert_state = AlertState.high
        elif channel.value < channel_config.alert_low_limit and channel_config.alert_low_enabled:
            channel.alert_state = AlertState.low
        else:
            channel.alert_state = AlertState.ok
        
        if not channel.alert_state == old_alert_state:
            channel.alert_ack = False
        
        self.db.session.commit()
        
        return True

    def get_colors_api(self):
        return jsonify([(color, webcolors.name_to_hex(color)) for color in PreferredColorList])

    def register_channel_api(self, module_id, channel_id):
        content = request.get_json() or request.form
        return jsonify(self.register(module_id, channel_id, content['unit']))

    def get_channels_api(self, module_id=None, channel_id=None):
        channels = self.get_channels(module_id, channel_id)
        if channels == None:
            abort(404)
        return jsonify(channels)

    def set_channels_api(self, module_id, channel_id):
        content = request.get_json() or request.form
        try:
            timestamp = content['timestamp']
        except KeyError:
            timestamp = None
        value = float(content['value'])

        return jsonify(self.process(module_id, channel_id, value, timestamp))

    def get_channel_config_api(self, module_id=None, channel_id=None):
        channel_config = self.get_channel_config(module_id, channel_id)
        if channel_config == None:
            abort(404)
        return jsonify(channel_config)

    def set_channel_config_api(self, module_id=None, channel_id=None):
        content = request.get_json() or request.form
        return jsonify(self.set_channel_config(content, module_id, channel_id))
