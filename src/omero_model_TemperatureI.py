#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2014 Glencoe Software, Inc. All Rights Reserved.
# Use is subject to license terms supplied in LICENSE.txt
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Code-generated omero.model.Temperature implementation,
based on omero.model.PermissionsI
"""


import Ice
import IceImport
IceImport.load("omero_model_Temperature_ice")
_omero = Ice.openModule("omero")
_omero_model = Ice.openModule("omero.model")
__name__ = "omero.model"

from omero_model_UnitBase import UnitBase
from omero.model.enums import UnitsTemperature


def noconversion(cfrom, cto):
    raise Exception(("Unsupported conversion: "
                     "%s:%s") % cfrom, cto)


class TemperatureI(_omero_model.Temperature, UnitBase):

    CONVERSIONS = dict()
    CONVERSIONS["DEGREEC:DEGREEF"] = \
        lambda: noconversion("DEGREEC", "DEGREEF")
    CONVERSIONS["DEGREEC:DEGREER"] = \
        lambda: noconversion("DEGREEC", "DEGREER")
    CONVERSIONS["DEGREEC:K"] = \
        lambda: noconversion("DEGREEC", "K")
    CONVERSIONS["DEGREEF:DEGREEC"] = \
        lambda: noconversion("DEGREEF", "DEGREEC")
    CONVERSIONS["DEGREEF:DEGREER"] = \
        lambda: noconversion("DEGREEF", "DEGREER")
    CONVERSIONS["DEGREEF:K"] = \
        lambda: noconversion("DEGREEF", "K")
    CONVERSIONS["DEGREER:DEGREEC"] = \
        lambda: noconversion("DEGREER", "DEGREEC")
    CONVERSIONS["DEGREER:DEGREEF"] = \
        lambda: noconversion("DEGREER", "DEGREEF")
    CONVERSIONS["DEGREER:K"] = \
        lambda: noconversion("DEGREER", "K")
    CONVERSIONS["K:DEGREEC"] = \
        lambda: noconversion("K", "DEGREEC")
    CONVERSIONS["K:DEGREEF"] = \
        lambda: noconversion("K", "DEGREEF")
    CONVERSIONS["K:DEGREER"] = \
        lambda: noconversion("K", "DEGREER")

    def __init__(self, value=None, unit=None):
        _omero_model.Temperature.__init__(self)
        if isinstance(value, _omero_model.TemperatureI):
            # This is a copy-constructor call.
            target = str(unit)
            source = str(value.getUnit())
            if target == source:
                self.setValue(value.getValue())
                self.setUnit(value.getUnit())
            else:
                c = self.CONVERSIONS.get("%s:%s" % (source, target))
                if c is None:
                    t = (value.getValue(), value.getUnit(), target)
                    msg = "%s %s cannot be converted to %s" % t
                    raise Exception(msg)
                self.setValue(c(value.getValue()))
                self.setUnit(UnitsTemperature.valueOf(target))
        else:
            self.setValue(value)
            self.setUnit(unit)

    def getUnit(self, current=None):
        return self._unit

    def getValue(self, current=None):
        return self._value

    def setUnit(self, unit, current=None):
        self._unit = unit

    def setValue(self, value, current=None):
        self._value = value

    def __str__(self):
        return self._base_string(self.getValue(), self.getUnit())

_omero_model.TemperatureI = TemperatureI
