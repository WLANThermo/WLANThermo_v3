#!/usr/bin/env python3
# coding=utf-8

from cerberus import schema_registry

__author__ = 'Björn Schrader <wlanthermo@bjoern-schrader.de>'
__license__ = 'GNU General Public License http://www.gnu.org/licenses/gpl.html'
__copyright__ = 'Copyright (C) 2017 by WLANThermo Project - Released under terms of the GPLv3 License'


# Fields in all sensor definitions
schema_registry.add('sensor', {
    'name': {'required': True, 'type': 'string'},
    'unit': {'required': True, 'type': 'string'},
    'type': {'required': True, 'type': 'string'},
})

# Fields in sensor definition for type 'voltage'
schema_registry.add('sensor_voltage', {
})

# Fields in sensor definition for type 'voltage'
schema_registry.add('sensor_resistance', {
})

# Fields in sensor definition for type 'ntc'
schema_registry.add('sensor_ntc', {
    'r_nominative': {'required': True, 'type': 'number'},
    'coeff_a' : {'required': True, 'type': 'number'},
    'coeff_b' : {'required': True, 'type': 'number'},
    'coeff_c' : {'required': True, 'type': 'number'},
    'coeff_d' : {'required': True, 'type': 'number'},
})

# Fields in sensor definition for type 'ntc_old'
schema_registry.add('sensor_ntc_old', {
    'r_nominative': {'required': True, 'type': 'number'},
    'coeff_a' : {'required': True, 'type': 'number'},
    'coeff_b' : {'required': True, 'type': 'number'},
    'coeff_c' : {'required': True, 'type': 'number'},
})

# Fields in sensor definition for type 'voltage'
schema_registry.add('sensor_rtd_pt', {
    'r_nominative': {'required': True, 'type': 'number'},
    'r_offset': {'required': True, 'type': 'number'},
})

# Fields in sensor definition for type 'poly_u'
schema_registry.add('sensor_poly_u', {
    'coeff_a': {'required': True, 'type': 'number'},
    'coeff_b': {'required': True, 'type': 'number'},
    'coeff_c': {'required': True, 'type': 'number'},
    'coeff_d': {'required': True, 'type': 'number'},
    'coeff_e': {'required': True, 'type': 'number'},
})

# Fields in sensor definition for type 'poly_r'
schema_registry.add('sensor_poly_r', {
    'coeff_a': {'required': True, 'type': 'number'},
    'coeff_b': {'required': True, 'type': 'number'},
    'coeff_c': {'required': True, 'type': 'number'},
    'coeff_d': {'required': True, 'type': 'number'},
    'coeff_e': {'required': True, 'type': 'number'},
})

# Fields in sensor definition for type 'tc'
schema_registry.add('sensor_tc', {
    'tc_type': {'required': True, 'type': 'string'},
})