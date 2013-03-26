#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/*
 *   Generated by blitz/templates/resouces/combined.vm
 *
 *   Copyright 2007 Glencoe Software, Inc. All rights reserved.
 *   Use is subject to license terms supplied in LICENSE.txt
 *
 */
"""

import omero.constants.permissions as ocp

import Ice, IceImport
IceImport.load("omero_model_Permissions_ice")
_omero = Ice.openModule("omero")
_omero_model = Ice.openModule("omero.model")
__name__ = "omero.model"

"""Permissions class which implements Unix-like rw logic for user/group/world.

>>> p = PermissionsI()
object #0 (::omero::model::Permissions)
{
    perm1 = -35
}
"""
class PermissionsI(_omero_model.Permissions):

      def __init__(self, l = None):
            super(PermissionsI, self).__init__()
            self.__immutable = False
            self._restrictions = None
            if isinstance(l, str):
                self._perm1 = -1
                self.from_string(l)
            elif l is not None:
                self._perm1 = long(l)
            else:
                self._perm1 = -1

      def granted(self, mask, shift):
            return (self._perm1 & (mask<<shift)) == (mask<<shift)

      def set(self, mask, shift, on):
            self.throwIfImmutable()
            if on:
                  self._perm1 = (self._perm1 | ( 0L | (mask<<shift)))
            else:
                  self._perm1 = (self._perm1 & (-1L ^ (mask<<shift)))

      # shift 8; mask 4
      def isUserRead(self):
            return self.granted(4,8)
      def setUserRead(self, value):
            self.set(4,8,value)

      # shift 8; mask 2
      def isUserWrite(self):
            return self.granted(2,8)
      def setUserWrite(self, value):
            self.set(2,8,value)

      # shift 8; mask 1
      def isUserAnnotate(self):
            return self.granted(1,8)
      def setUserAnnotate(self, value):
            self.set(1,8,value)

      # shift 4; mask 4
      def isGroupRead(self):
            return self.granted(4,4)
      def setGroupRead(self, value):
            self.set(4,4,value)

      # shift 4; mask 2
      def isGroupWrite(self):
            return self.granted(2,4)
      def setGroupWrite(self, value):
            self.set(2,4,value)

      # shift 4; mask 1
      def isGroupAnnotate(self):
            return self.granted(1,4)
      def setGroupAnnotate(self, value):
            self.set(1,4,value)

      # shift 0; mask 4
      def isWorldRead(self):
            return self.granted(4,0)
      def setWorldRead(self, value):
            self.set(4,0,value)

      # shift 0; mask 2
      def isWorldWrite(self):
            return self.granted(2,0)
      def setWorldWrite(self, value):
            self.set(2,0,value)

      # shift 0; mask 1
      def isWorldAnnotate(self):
            return self.granted(1,0)
      def setWorldAnnotate(self, value):
            self.set(1,0,value)

      # Calculated values

      def isDisallow(self, restriction, current=None):
          rs = self._restrictions
          if rs is not None and len(rs) > restriction:
                return rs[restriction]
          return False

      def canAnnotate(self, current=None):
          return not self.isDisallow(ocp.ANNOTATERESTRICTION)

      def canDelete(self, current=None):
          return not self.isDisallow(ocp.DELETERESTRICTION)

      def canEdit(self, current=None):
          return not self.isDisallow(ocp.EDITRESTRICTION)

      def canLink(self, current=None):
          return not self.isDisallow(ocp.LINKRESTRICTION)

      # Accessors; do not use

      def getPerm1(self):
          return self._perm1

      def setPerm1(self, _perm1):
          self.throwIfImmutable()
          self._perm1 = _perm1
          pass

      def from_string(self, perms):
          """
          Sets the state of this instance via the 'perms' string.
          Returns 'self'. Also used by the constructor which
          takes a string.
          """
          import re
          base = "([rR\-_])([aAwW\-_])"
          regex = re.compile("^(L?)%s$" % (base*3))
          match = regex.match(perms)
          if match is None:
            raise ValueError("Invalid permission string: %s" % perms)
          l = match.group(1)
          ur = match.group(2)
          uw = match.group(3)
          gr = match.group(4)
          gw = match.group(5)
          wr = match.group(6)
          ww = match.group(7)
          # User
          self.setUserRead(ur.lower() == "r")
          self.setUserAnnotate(uw.lower() == "a")
          if uw.lower() == "w":
              self.setUserAnnotate(True) # w implies a
              self.setUserWrite(True)
          else:
              self.setUserWrite(False)
          # Group
          self.setGroupRead(gr.lower() == "r")
          self.setGroupAnnotate(gw.lower() == "a")
          if gw.lower() == "w":
              self.setGroupAnnotate(True) # w implies a
              self.setGroupWrite(True)
          else:
              self.setGroupWrite(False)
          # World
          self.setWorldRead(wr.lower() == "r")
          self.setWorldAnnotate(ww.lower() == "a")
          if ww.lower() == "w":
              self.setWorldAnnotate(True) # w implies a
              self.setWorldWrite(True)
          else:
              self.setWorldWrite(False)

          return self

      def __str__(self):
          vals = []
          # User
          vals.append(self.isUserRead() and "r" or "-")
          if self.isUserWrite():
              vals.append("w")
          elif self.isUserAnnotate():
              vals.append("a")
          else:
              vals.append("-")
          # Group
          vals.append(self.isGroupRead() and "r" or "-")
          if self.isGroupWrite():
              vals.append("w")
          elif self.isGroupAnnotate():
              vals.append("a")
          else:
              vals.append("-")
          # World
          vals.append(self.isWorldRead() and "r" or "-")
          if self.isWorldWrite():
              vals.append("w")
          elif self.isWorldAnnotate():
              vals.append("a")
          else:
              vals.append("-")
          return "".join(vals)

      def throwIfImmutable(self):
          """
          Check the __immutable field and throw a ClientError
          if it's true.
          """
          if self.__immutable:
              raise _omero.ClientError("ImmutablePermissions: %s" % \
                      self.__str__())

      def ice_postUnmarshal(self):
          """
          Provides additional initialization once all data loaded
          Required due to __getattr__ implementation.
          """
          #_omero_model.Permissions.ice_postUnmarshal(self)
          self.__immutable = True

      def ice_preMarshal(self):
          """
          Provides additional validation before data is sent
          Required due to __getattr__ implementation.
          """
          pass # Currently unused

      def __getattr__(self, attr):
          if attr == "perm1":
              return self.getPerm1()
          else:
              raise AttributeError(attr)

      def  __setattr__(self, attr, value):
        if attr.startswith("_"):
            self.__dict__[attr] = value
        else:
            try:
                object.__getattribute__(self, attr)
                object.__setattr__(self, attr, value)
            except AttributeError:
                if attr == "perm1":
                    return self.setPerm1(value)
                else:
                    raise

_omero_model.PermissionsI = PermissionsI

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
