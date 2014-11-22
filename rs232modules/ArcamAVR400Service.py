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

M_ZONE = 1
M_CMD = 2
M_AC = 3
M_DL = 4
M_DATA = 5
M_DATA_END = -1

def _or_unknown(dictionary, message, idx=M_DATA):
  if ord(message[idx]) in dictionary:
    return dictionary[ord(message[idx])]
  else:
    return "Unknown: " + str(hex(ord(message[idx])))

class ArcamAVR400Service(BaseService):

  def __init__(self, tty, bus_name):
    self.lock = RLock()
    self.all_commands = dict([item for sublist in [a_cmds.commands[x].items() for x in a_cmds.commands] for item in sublist])

    BaseService.__init__(self, bus_name, ARCAMAVR400SERVICE_OBJ_PATH, tty, BAUD_RATE, self, a_cmds)

  def help(self):
    string = ""
    for group in self.cmds.commands:
      string += '\n' + group
      for command in self.cmds.commands[group]:
        string += "\n  " + command + ": " + self.cmds.commands[group][command][0]
    return string[1:]

  @dbus.service.method(ARCAMAVR400SERVICE_IFACE, in_signature='ssb', out_signature='s')
  def send_cmd(self, cmd, argument, check):
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
      else:
        return "Invalid argument (" + argument + "): " + str(our_cmd[3]())
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
              returnable += "  " + str(key) + ": " + str(zone[key]) + "\n"
          else:
            returnable += "No information on zone: " + str(idx) + "\n"
    except:
      self.logger.exception("Exception in status")
    return returnable

  def answer_code(self, message):
    return a_cmds.answer_code[ord(message[M_AC])] 

  def parse_message_default(self, message):
    # default
    with self.lock:
      zones[ord(message[M_ZONE])][hex(ord(message[M_CMD]))]= (str([hex(ord(x)) for x in message[M_DATA : M_DATA_END ]]), self.answer_code(message))

  def parse_message_power(self, message):
    # Power
    with self.lock:
      zones[ord(message[M_ZONE])]["Powered"] = (str(True if ord(message[M_DATA]) == 0x01 else False), self.answer_code(message))

  def parse_message_display_brightness(self, message):
    # Display Brightness
    with self.lock:
      zones[ord(message[M_ZONE])]["Display Brightness"] = (
          _or_unknown(a_cmds.display_brightness, message),
          self.answer_code(message))

  def parse_message_headphones_connected(self, message):
    # Headphones Connected
    with self.lock:
      zones[ord(message[M_ZONE])]["Headphones"] = (
          ("not " if ord(message[M_DATA]) == 0x00 else "") + "connected",
          self.answer_code(message))

  def parse_message_fm_genre(self, message):
    #FM Genre
    with self.lock:
      zones[ord(message[M_ZONE])]["FM Genre"] = (
          str(message[M_DATA:-1]),
          self.answer_code(message))

  def parse_message_rds_information(self, message):
    #RDS Information
    with self.lock:
      zones[ord(message[M_ZONE])]["RDS Information"] = (
          str(message[M_DATA:-1]),
          self.answer_code(message))

  def parse_message_version(self, message):
    #Version
    with self.lock:
      zones[ord(message[M_ZONE])][_or_unknown(a_cmds.version_software, message) + " version"] = (
          str(ord(message[M_DATA + 1])) + "." + str(ord(message[M_DATA + 2])),
          self.answer_code(message))

  def parse_message_volume(self, message):
    # Volume
    with self.lock:
      zones[ord(message[M_ZONE])]["Volume"] = (str(ord(message[M_DATA])), self.answer_code(message))

  def parse_message_mute(self, message):
    # Mute
    with self.lock:
      zones[ord(message[M_ZONE])]["Muted"] = (str(True if ord(message[M_DATA]) == 0x00 else False), self.answer_code(message))

  def parse_message_direct(self, message):
    # Mute
    with self.lock:
      zones[ord(message[M_ZONE])]["Direct Mode"] = (str(True if ord(message[M_DATA]) == 0x01 else False), self.answer_code(message))

  def parse_message_video_resolution(self, message):
    # Video Resolution
    with self.lock:
      zones[ord(message[M_ZONE])]["Video Resolution"] = (_or_unknown(a_cmds.video_resolutions, message),
          self.answer_code(message))

  def parse_message_menu_status(self, message):
    with self.lock:
      zones[ord(message[M_ZONE])]["Menu"] = (
          _or_unknown(a_cmds.menu_status, message),
          self.answer_code(message))


  def parse_message_source(self, message):
    # Current Source
    with self.lock:
      zones[ord(message[M_ZONE])]["Source"] = (
          _or_unknown(a_cmds.source, message),
          self.answer_code(message))

  def parse_message_video(self, message):
    # Video Selection
    with self.lock:
      zones[ord(message[M_ZONE])]["Video"] = (
          _or_unknown(a_cmds.video, message),
          self.answer_code(message))

  def parse_message_analogue(self, message):
    # Analogue/Digital Selection
    with self.lock:
      zones[ord(message[M_ZONE])]["Analogue"] = (
          _or_unknown(a_cmds.analogue, message),
          self.answer_code(message))

  def parse_message_video_input(self, message):
    # Video Selection
    with self.lock:
      zones[ord(message[M_ZONE])]["Video input type"] = (
          _or_unknown(a_cmds.video_input, message),
          self.answer_code(message))

  def parse_message_decode_mode_2ch(self, message):
    # Decode Mode Status - 2ch
    with self.lock:
      zones[ord(message[M_ZONE])]["2ch Decode Mode"] = (
          _or_unknown(a_cmds.decode_mode_2ch, message),
          self.answer_code(message))

  def parse_message_decode_mode_mch(self, message):
    # Decode Mode Status - Mch
    with self.lock:
      zones[ord(message[M_ZONE])]["Mch Decode Mode"] = (
          _or_unknown(a_cmds.decode_mode_mch, message),
          self.answer_code(message))

  def parse_message_simulate_rc5(self, message):
    # Simulate RC
    with self.lock:
      zones[ord(message[M_ZONE])]["Simulate RC5"] = (
          a_cmds.simulate_rc5[(ord(message[M_DATA]), ord(message[M_DATA + 1]))],
          self.answer_code(message))

  def parse_message_treble(self, message):
    # 0x35
    with self.lock:
      treble = ord(message[M_DATA]) if ord(message[M_DATA]) < 0x0d else (0x80 - ord(message[M_DATA]))
      zones[ord(message[M_ZONE])]["Treble"] = (
          str(treble),
          self.answer_code(message))

  def parse_message_bass(self, message):
    # 0x36
    with self.lock:
      bass = ord(message[M_DATA]) if ord(message[M_DATA]) < 0x0a else (0x80 - ord(message[M_DATA]))
      zones[ord(message[M_ZONE])]["Bass"] = (
          str(bass),
          self.answer_code(message))

  def parse_message_room(self, message):
    # 0x37
    with self.lock:
      roomeq = {
          0x00: 'Off',
          0x01: 'On',
          0x02: 'Not calculated (therefore Off)'
      }
      zones[ord(message[M_ZONE])]["Room Equalisation"] = (
          _or_unknown(roomeq, message),
          self.answer_code(message))

  def parse_message_dolby_volume(self, message):
    # 0x38
    with self.lock:
      zones[ord(message[M_ZONE])]["Dolby Volume"] = (str("On" if ord(message[M_DATA]) == 0x01 else "Off"), self.answer_code(message))

  def parse_message_dolby_leveller(self, message):
    # 0x39
    with self.lock:
      leveller = ord(message[M_DATA]) if ord(message[M_DATA]) < 0x0a else "Off"
      zones[ord(message[M_ZONE])]["Dolby Leveller"] = (
          str(leveller),
          self.answer_code(message))

  def parse_message_incoming_audio_format(self, message):
    # 0x43
    with self.lock:
      zones[ord(message[M_ZONE])]["Audio stream format"] = (
          _or_unknown(a_cmds.inc_audio_stream, message),
          self.answer_code(message))
      zones[ord(message[M_ZONE])]["Audio stream channel configuration"] = (
          _or_unknown(a_cmds.inc_audio_channel, message, idx=M_DATA + 1),
          self.answer_code(message))

  def parse_message(self, message):
    try:
      self.logger.debug("Parsing message: " + str([hex(ord(x)) for x in message]))
      if ord(message[M_CMD]) in a_cmds.responses and hasattr(self, "parse_message_" + a_cmds.responses[ord(message[M_CMD])]):
        self.logger.debug("Parse_message_" + a_cmds.responses[ord(message[M_CMD])])
        getattr(self, "parse_message_" + a_cmds.responses[ord(message[M_CMD])])(message)
      else:
        self.logger.debug("Parse_message_default " + hex(ord(message[M_CMD])))
        self.parse_message_default(message)
      return self.answer_code(message)
    except:
      self.logger.exception("Failed to parse message")
      self.logger.info(str([hex(ord(x)) for x in message]))
      return "Failed to parse message"

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
    return self.parse_message(message)

  def read(self, serial, all_commands=False):
    serial.timeout = None
    message = self.read_message(serial)
    return message
