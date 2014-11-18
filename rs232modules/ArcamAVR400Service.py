#!/usr/bin/env python2

# Copyright (C) 2011,2012,2013 Brendan Le Foll <brendan@fridu.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from SerialController import SerialController
from BaseService import BaseService

import arcamAVR400_cmds

ARCAMAVR400SERVICE_IFACE = 'uk.co.madeo.rs232server.arcamAVR400'
ARCAMAVR400SERVICE_OBJ_PATH = '/uk/co/madeo/rs232server/arcamAVR400'

DELAY = 1
BAUD_RATE = 38400
BYTESIZE = 8
READVAL = 10

class ArcamAVR400Service(BaseService):

  def __init__(self, tty, bus_name):
    BaseService.__init__(self, bus_name, ARCAMAVR400SERVICE_OBJ_PATH, tty, BAUD_RATE, READVAL, arcamAVR400_cmds)

  @dbus.service.method(ARCAMAVR400SERVICE_IFACE, in_signature='sib', out_signature='s')
  def send_cmd(self, cmd, repeat, check):
    self.logger.debug("sent command : %s", cmd)
    if cmd == "help":
      self.logger.debug("Getting help!")
      return self.help()
    if (check):
      val = self.queue.add(arcamAVR400_cmds.commands[cmd].decode('ascii'), check)
      return str([hex(ord(x)) for x in val])
    for i in range(0, repeat):
      self.queue.add(arcamAVR400_cmds.commands[cmd].decode('ascii'), check)
    return ""
