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

import sys
import time
import Queue
import logging
import serial
import Shared
from threading import Thread
from threading import Timer

DELAY = 0.05
MAXCMDS = 0
STRIPPING_ERROR = 999

class SerialController:

  def __init__(self, ser, readval):
    self.serial_logger = logging.getLogger(Shared.APP_NAME + '.' + self.__class__.__name__)
    self.setup_serial(ser)
    self.readval = readval
    self.serial_logger.debug("Serial is %s", str(ser))

    # set up queue and start queue monitoring thread
    self.queue = Queue.Queue()
    self.t = Thread(target=self.monitor)
    self.t.daemon = True
    self.t.start()

    # set up reader thread
    self.ser.timeout = None
    self.reader = Thread(target=self.read_monitor)
    self.reader.daemon = True
    self.reader.start()

  def setup_serial(self, ser):
    self.ser = ser
    self.ser.flushInput()
    self.ser.flushOutput()
    self.serial_logger.debug("Initialised %s with baud rate %d", ser.name, ser.baudrate)

  def read(self, all_entries=False):
    try:
      if (hasattr(self.readval, "read")):
        return self.readval.read(self.ser, all_entries)
      else:
        if (all_entries):
          return self.ser.read(self.ser.inWaiting() or self.readVal)
        else:
          return self.ser.read(self.readval)
    except:
      self.serial_logger.exception("Failed to read from the serial buffer")

  def cmd(self, cmd, read=False):
    try:
      if cmd is not "clear":
        numBytes = self.ser.write(cmd)
        self.serial_logger.debug("Wrote %d bytes", numBytes)
        self.serial_logger.debug (str([hex(ord(x)) for x in cmd]) + " called")
        self.ser.flush()
        #if read:
        #  code = self.read()
        #  return code
      else:
        self.serial_logger.debug ("Clearing read buffer")
        self.ser.flush()
        self.ser.flushOutput()
        #self.ser.flushInput()
        #waiting = self.ser.inWaiting()
        #if (waiting > 0):
        #  self.read(True)
    except:
      self.serial_logger.error ("%s call failed", cmd.rstrip())

  def monitor(self):
    while True:
      item = self.queue.get()
      self.cmd(item)
      self.queue.task_done()
      self.ser.flush()

  def read_monitor(self):
    while True:
      self.read(True)

  def add(self, cmd, direct=False):
    if direct:
      # direct execution allows for return
      return self.cmd(cmd, True)
    else:
      self.queue.put(cmd, True)
      # delay here seems to allow the monitor thread to come to life on my single core CPU
      time.sleep(DELAY)
