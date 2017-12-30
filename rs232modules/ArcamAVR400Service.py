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
from threading import RLock

import arcamAVR400_cmds as a_cmds

ARCAMAVR400SERVICE_IFACE = 'uk.co.madeo.rs232server.arcamAVR400'
ARCAMAVR400SERVICE_OBJ_PATH = '/uk/co/madeo/rs232server/arcamAVR400'

DELAY = 1
BAUD_RATE = 38400
BYTESIZE = 8
READVAL = 10
ST=chr(0x21)
ET=chr(0x0d)
zones = { 0x01: {}, 0x02: {}}

def _or_unknown(dictionary, key):
  if key in dictionary:
    return dictionary[key]
  else:
    return "Unknown: " + str(hex(key))

class Message:
  M_ZONE = 1
  M_CMD = 2
  M_AC = 3
  M_DL = 4
  M_DATA = 5
  M_DATA_END = -1
  def __init__(self, message):
    self.zone = ord(message[self.M_ZONE])
    self.command = ord(message[self.M_CMD])
    self.answer_code = ord(message[self.M_AC])
    self.data_length = ord(message[self.M_DL])
    self.data = message[self.M_DATA: self.M_DATA_END]
    self.raw = message

  def int_value(self, max_val=0x0c):
    return str(ord(self.data[0]) if ord(self.data[0]) <= max_val else (0x80 - ord(self.data[0])))

  def dict_or_unknown(self, dictionary, idx=0):
    return _or_unknown(dictionary, ord(self.data[idx]))

  def hex_string(self):
    return str([hex(ord(x)) for x in self.data])

  def string_value(self):
    return str(self.data),

class ArcamAVR400Service(BaseService):

  def __init__(self, tty, bus_name):
    self.lock = RLock()
    self.all_commands = dict([item for sublist in [a_cmds.commands[x].items() for x in a_cmds.commands] for item in sublist])

    BaseService.__init__(self, bus_name, ARCAMAVR400SERVICE_OBJ_PATH, tty, BAUD_RATE, self, a_cmds)

  def help(self):
    string = ""
    for group in a_cmds.commands.keys():
      string += '\n' + group
      for (name, command) in self.cmds.commands[group].items():
        if (command[1] == "1"):
          string += "\n  " + name + " <argument>: " + command[0] + "\n    " + str(command[3]())
        elif (command[1] == "?"):
          string += "\n  " + name + " [<argument>]: " + command[0] + "\n    " + str(command[3]())
        else:
          string += "\n  " + name + ": " + command[0]
    return string[1:]

  @dbus.service.method(ARCAMAVR400SERVICE_IFACE, in_signature='ssb', out_signature='s')
  def send_cmd(self, cmd, argument, check):
    try:
      self.logger.debug("sent command : %s, %s, %s", cmd, argument, check)
      if cmd == "help":
        self.logger.debug("Getting help!")
        return self.help()
      if cmd == "status":
        self.logger.debug("Getting status")
        return self.status()
      our_cmd = self.all_commands[cmd]
      if (our_cmd[1] == 0):
        if (argument and argument != ""):
          try:
            repeat = int(argument)
            for i in range(0, repeat):
              self.queue.add(our_cmd[2], check)
          except ValueError:
            self.queue.add(our_cmd[2], check)
        else:
          self.queue.add(our_cmd[2], check)
      else:
        if (argument and argument != "" and our_cmd[3](argument)):
          self.queue.add(our_cmd[2](argument), check)
        elif (our_cmd[1] == '?'):
          self.queue.add(our_cmd[2](), check)
        else:
          return "Invalid argument (" + argument + "): " + str(our_cmd[3]())
    except:
      self.logger.exception("Exception in send_cmd")
    return ""

  def status(self):
    returnable = "ArcamAVR400 Service:\n"
    try:
      with self.lock:
        self.logger.debug("In Status")
        for (idx, zone) in zones.items():
          if (len(zone) > 0):
            returnable += "Zone: " + str(idx) + "\n"
            for key in sorted(zone.keys(), key = lambda x : ('z' + str(x)) if str(x).upper() < 'A' else str(x).upper()):
              returnable += "  " + str(key) + ": " + str(zone[key][0]) + ( (" - " + _or_unknown(a_cmds.answer_code, zone[key][1])) if zone[key][1] != 0x00 else "") + "\n"
          else:
            returnable += "No information on zone: " + str(idx) + "\n"
    except:
      self.logger.exception("Exception in status")
    return returnable

  def answer_code(self, message):
    if a_cmds.answer_code.has_key(message.answer_code):
        return a_cmds.answer_code[message.answer_code]
    else:
        return hex(message.answer_code) + ': Unknown Code'

  def set_zone(self, zone, name, value, answer_code):
    with self.lock:
      zones[zone][name] = (value, answer_code)

  def parse_message_default(self, message):
    # default
    self.set_zone(message.zone, hex(message.command), message.hex_string(), message.answer_code)

  def parse_message(self, message):
    with self.lock:
      self.logger.debug("Parsing message: " + str([hex(ord(x)) for x in message.raw]))
      if message.command in a_cmds.responses:
        if callable(a_cmds.responses[message.command]):
          a_cmds.responses[message.command](self.set_zone, message)
          return self.answer_code(message)
        elif hasattr(self, "parse_message_" + a_cmds.responses[message.command]):
          self.logger.debug("Parse_message_" + a_cmds.responses[message.command])
          getattr(self, "parse_message_" + a_cmds.responses[message.command])(message)
          return self.answer_code(message)
      self.logger.debug("Parse_message_default " + hex(message.command))
      self.parse_message_default(message)
      return self.answer_code(message)

  def read_message(self, serial):
    message = serial.read(5)
    last = ET
    if not(message[0] == ST):
      self.logger.info("Starting read in middle of command stream.")
      self.logger.debug(str([hex(ord(x)) for x in message]))
      while(message[0] != ST and last != ET):
        last = message[0]
        self.logger.debug("Throwing away... " + str(hex(ord(last))))
        message = message[1:] + serial.read(1)
    message += serial.read(ord(message[4]) + 1)
    try:
      return self.parse_message(Message(message))
    except:
      self.logger.exception("Failed to parse message")
      self.logger.info(str([hex(ord(x)) for x in message]))
      return "Failed to parse message"

  def read(self, serial, all_commands=False):
    serial.timeout = None
    message = self.read_message(serial)
    return message
