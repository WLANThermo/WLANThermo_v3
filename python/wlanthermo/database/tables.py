#!/usr/bin/env python3
# coding=utf-8

import datetime
import enum
import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext import mutable
from sqlalchemy import inspect, TypeDecorator, Column, Integer, String, ForeignKey, DateTime, Enum, Float, Boolean, JSON
from sqlalchemy.orm import relationship

__author__ = 'Björn Schrader <wlanthermo@bjoern-schrader.de>'
__license__ = 'GNU General Public License http://www.gnu.org/licenses/gpl.html'
__copyright__ = 'Copyright (C) 2017 by WLANThermo Project - Released under terms of the GPLv3 License'

Base = declarative_base()

class ChannelType(enum.Enum):
    channel_data = 1
    pitmaster_data = 2


class AlertState(enum.IntEnum):
    none = 0
    ok = 1
    high = 2
    low = 3


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


class Dictable():
    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

class JsonEncoded(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""
    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class SettingsTable(Base, Dictable):
    """Die aktuellen Kanaldaten
    """
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    scope = Column(String(50))
    key = Column(String(50))
    value = Column(JsonEncoded(200))


class ChannelsTable(Base, Dictable):
    """Die aktuellen Kanaldaten
    """
    __tablename__ = 'channels'
    id = Column(Integer, primary_key=True)
    config_id = Column(Integer, ForeignKey('channel_config.id'))
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    alert_state = Column(Enum(AlertState), default=AlertState.none)
    alert_ack = Column(Boolean, default=False)


class ChannelConfigTable(Base, Dictable):
    """Die aktuelle Kanalkonfiguration
    """
    __tablename__ = 'channel_config'
    id = Column(Integer, primary_key=True)
    type = Column(Enum(ChannelType))
    module_id = Column(Integer)
    channel_id = Column(Integer)
    name = Column(String(50))
    unit = Column(String(20))
    sensor_type = Column(String(20), default='none')
    alert_low_limit = Column(Float, default=-20)
    alert_high_limit = Column(Float, default=200)
    alert_low_enabled = Column(Boolean, default=False)
    alert_high_enabled = Column(Boolean, default=False)
    color = Column(String(20), default='#000000')
    description = Column(String(500), default='')


class ModulesTable(Base, Dictable):
    """Die aktuellen Kanaldaten
    """
    __tablename__ = 'modules'
    id = Column(Integer, primary_key=True)
    name = Column(String(40))
    registered = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    sensor_types = Column(JsonEncoded(200))


class LogList(Base, Dictable):
    """Liste der Vergrillungen
    """
    __tablename__ = 'log_list'
    log_id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    title = Column(String(50))
    description = Column(String(500))


class LogModules(Base, Dictable):
    """Liste der Module
    """
    __tablename__ = 'log_modules'
    id = Column(Integer, primary_key=True)
    log_id = Column(Integer, ForeignKey('log_list.log_id'))
    module_id = Column(Integer)
    module_name = Column(String(30))


class LogChannels(Base, Dictable):
    """Die Metadaten der geloggten Kanäle
    """
    __tablename__ = 'log_channels'
    pen_id = Column(Integer, primary_key=True)
    log_id = Column(Integer, ForeignKey('log_list.log_id'))
    type = Column(Enum(ChannelType))
    module_id = Column(Integer)
    channel_id = Column(Integer)
    name = Column(String(50))
    description = Column(String(500))
    alert_thresholds = relationship(
        "LogAlertThresholds", order_by="desc(LogAlertThresholds.timestamp)", back_populates="channel")


class LogUnits(Base, Dictable):
    """Die Metadaten der geloggten Kanäle
    """
    __tablename__ = 'log_units'
    id = Column(Integer, primary_key=True)
    pen_id = Column(Integer, ForeignKey('log_channels.pen_id'))
    unit = Column(String(30))
    timestamp = Column(DateTime)


class LogAlertThresholds(Base, Dictable):
    """Grenzwerte inkl. Änderungen
    """
    __tablename__ = 'log_alert_thresholds'
    id = Column(Integer, primary_key=True)
    pen_id = Column(Integer, ForeignKey('log_channels.pen_id'))
    channel = relationship("LogChannels", back_populates="alert_thresholds")
    timestamp = Column(DateTime)
    alert_high_limit = Column(Float)
    alert_high_enabled = Column(Boolean)
    alert_low_limit = Column(Float)
    alert_low_enabled = Column(Boolean)


class LogData(Base, Dictable):
    """Geloggte Daten
    """
    __tablename__ = 'log_data'
    id = Column(Integer, primary_key=True)
    pen_id = Column(Integer, ForeignKey('log_channels.pen_id'))
    timestamp = Column(DateTime)
    value = Column(Float)
    alert_state = Column(Enum(AlertState))


class LogEvents(Base, Dictable):
    """Eventtypen
    """
    __tablename__ = 'log_events'
    id = Column(Integer, primary_key=True)
    log_id = Column(Integer, ForeignKey('log_list.log_id'))
    description = Column(String(500))
    icon = Column(String(30))


class LogAnnotations(Base, Dictable):
    """Besondere Anmerkungen zum Verlauf
    """
    __tablename__ = 'log_annotations'
    id = Column(Integer, primary_key=True)
    log_id = Column(Integer, ForeignKey('log_list.log_id'))
    event_id = Column(Integer, ForeignKey('log_events.id'))
    timestamp = Column(DateTime)
    description = Column(String(500))


class LogChannelAnnotations(Base, Dictable):
    """Besondere Anmerkungen zu einzelnen Kanälen
    """
    __tablename__ = 'log_channel_annotations'
    id = Column(Integer, primary_key=True)
    log_id = Column(Integer, ForeignKey('log_list.log_id'))
    pen_id = Column(Integer, ForeignKey('log_channels.pen_id'))
    event_id = Column(Integer, ForeignKey('log_events.id'))
    timestamp = Column(DateTime)
    description = Column(String(500))
