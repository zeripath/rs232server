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

start = "\x21" # PC_
end = "\x0d" # <CR>

zone_1 = "\x01"
zone_2 = "\x02"

simulate_rc5 = "\x08\x02"

commands = {
#volume
  'voldown':  start + zone_1 + simulate_rc5 + "\x10\x11" + end,
  'volup':    start + zone_1 + simulate_rc5 + "\x10\x10" + end,
  'mute':     start + zone_1 + simulate_rc5 + "\x10\x77" + end,
  'unmute':   start + zone_1 + simulate_rc5 + "\x10\x78" + end,
#power
  'poweron':  start + zone_1 + simulate_rc5 + "\x10\x7b" + end,
  'poweroff': start + zone_1 + simulate_rc5 + "\x10\x7c" + end,
#inputs
  'dvd':      start + zone_1 + simulate_rc5 + "\x10\x04" + end,
  'sat':      start + zone_1 + simulate_rc5 + "\x10\x00" + end,
  'av':       start + zone_1 + simulate_rc5 + "\x10\x02" + end,
  'pvr':      start + zone_1 + simulate_rc5 + "\x10\x22" + end,
  'vcr':      start + zone_1 + simulate_rc5 + "\x10\x06" + end,
  'cd':       start + zone_1 + simulate_rc5 + "\x10\x07" + end,
  'tuner':    start + zone_1 + simulate_rc5 + "\x10\x03" + end,
  'net':      start + zone_1 + simulate_rc5 + "\x10\x0b" + end,
  'ipod':     start + zone_1 + simulate_rc5 + "\x10\x12" + end,
#tuner
  'am':       start + zone_1 + simulate_rc5 + "\x11\x35" + end,
  'fm':       start + zone_1 + simulate_rc5 + "\x11\x34" + end,
  'net':      start + zone_1 + simulate_rc5 + "\x11\x7e" + end,
#two-channel modes
  "directmodeon":  start + zone_1 + simulate_rc5 + "\x10\x4e" + end,
  "directmodeoff": start + zone_1 + simulate_rc5 + "\x10\x67" + end,
  "pl2movie":      start + zone_1 + simulate_rc5 + "\x10\x67" + end,
  "pl2music":      start + zone_1 + simulate_rc5 + "\x10\x68" + end,
  "pl2game":       start + zone_1 + simulate_rc5 + "\x10\x66" + end,
  "neo6cinema":    start + zone_1 + simulate_rc5 + "\x10\x6f" + end,
  "neo6music":     start + zone_1 + simulate_rc5 + "\x10\x70" + end,
  "dolbyex":       start + zone_1 + simulate_rc5 + "\x10\x76" + end,
#surround modes
  "stereo":    start + zone_1 + simulate_rc5 + "\x10\x6b" + end,
  "mchmode":       start + zone_1 + simulate_rc5 + "\x10\x6a" + end,
  "pl2mode":   start + zone_1 + simulate_rc5 + "\x10\x6e" + end,
}

responses = {
}
