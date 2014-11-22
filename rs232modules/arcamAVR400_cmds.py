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

start = "\x21" # !
end = "\x0d" # <CR>

zone_1 = "\x01"
zone_2 = "\x02"

simulate_rc5 = "\x08\x02"

version_strings = {
  "rs232": '\xf0',
  "mcu": '\xf1',
  "torino": '\xf2',
  "dsp": '\xf3',
  "usb": '\xf4',
  "submcu": '\xf5'
}
room_eq_on_off = { 'current': '\xf0', 'on': '\xf1', 'off': '\xf2' }

dolby_volume_on_off = { 'current': '\xf0', 'on': '\x01', 'off': '\x00' }

def volume_check(x=None):
  if x is not None:
    try:
      return int(x) < 99 and int(x) >= 0
    except ValueError:
      if x == "current":
        return 0xf0
      return false
  else:
    return "[0...99 | current]"

video_resolutions = {
  0x01: "SD Interlaced",
  0x02: "SD Progressive",
  0x03: "720p",
  0x04: "1080i",
  0x05: "1080p",
  0x06: "Preferred",
  0x07: "Bypass",
  0xF0: "Current",
  0xF1: "Increment",
  0xF2: "Decrement",
}
video_resolutions_to_num = {
  "sd_interlaced": 0x01,
  "sd_progressive": 0x02,
  "720p": 0x03,
  "1080i": 0x04,
  "1080p": 0x05,
  "preferred": 0x06,
  "bypass": 0x07,
  "current": 0xF0,
  "increment": 0xF1,
  "decrement": 0xF2,
}

def parse_treble(x):
  try:
    val = int(x)
    if (val > 0x0c):
      return chr(0xf0)
    elif (val <= 0x0c and val >= 0):
      return chr(val)
    else:
      val = 0x80 - val
      if (val > 0x8c):
        return chr(0xf0)
      else:
        return chr(val)
  except ValueError:
    if x.lower() == 'current':
      return chr(0xf0)
    elif x.lower() == 'increment':
      return chr(0xf1)
    elif x.lower() == 'decrement':
      return chr(0xf2)
    return chr(0xf0)

def check_treble(x=None):
  if x is not None:
    val = parse_treble(x)
    if (ord(val) == 0xf0 and not x.lower() == 'current'):
      return False
    return True
  else:
    return '[ 0..12 | -1..-12 | current | increment | decrement]'

def parse_leveller(x):
  try:
    val = int(x)
    if (val <= 0x0a and val >= 0):
      return chr(val)
    return chr(0xf0)
  except ValueError:
    if x.lower() == 'current':
      return chr(0xf0)
    elif x.lower() == 'increment':
      return chr(0xf1)
    elif x.lower() == 'decrement':
      return chr(0xf2)
    elif x.lower() == 'off':
      return chr(0xff)
    return chr(0xf0)

def check_leveller(x=None):
  if x is not None:
    val = parse_leveller(x)
    if (ord(val) == 0xf0 and not x.lower() == 'current'):
      return False
    return True
  else:
    return '[ 0..10 | current | increment | decrement | off]'

commands = { 'State': {
    'power':          ("Get current power state", 0, start + zone_1 + "\x00\x01\xf0" + end),
    'display_brightness':   ("Get display brightness", 0, start + zone_1 + "\x01\x01\xf0" + end),
    'headphones_connected': ("Get headphone connection", 0, start + zone_1 + "\x02\x01\xf0" + end),
    'fm_genre':             ("Get FM Genre", 0, start + zone_1 + "\x03\x01\xf0" + end),
    'source':               ("Get Current Source", 0, start + zone_1 + "\x1d\x01\xf0" + end),
    'version':              ("Get Software Version", 1,
      lambda x : (start + zone_1 + "\x04\x01" + version_strings[x.lower()] + end),
      lambda x=None: x.lower() in version_strings if x is not None else version_strings.keys()),
    'decode_mode_2ch':      ("Get 2ch Decode Mode", 0, start + zone_1 + "\x10\x01\xf0" + end),
    'decode_mode_mch':      ("Get Mch Decode Mode", 0, start + zone_1 + "\x11\x01\xf0" + end),
    'rds_information':      ("Get RDS Information", 0, start + zone_1 + "\x12\x01\xf0" + end),
    'menu_status':          ("Get current menu status", 0, start + zone_1 + "\x14\x01\xf0" + end),
  }, 'Volume': {
    'volume':   ("Get/Set Volume", 1,
      lambda x : (start + zone_1 + "\x0d\x01" + (chr(0xf0) if x == "current" else chr(int(x)) ) + end),
      volume_check),
    'voldown':  ("Decrease Volume", 0, start + zone_1 + simulate_rc5 + "\x10\x11" + end),
    'volup':    ("Increase Volume", 0, start + zone_1 + simulate_rc5 + "\x10\x10" + end),
    'mute':     ("Mute", 0, start + zone_1 + simulate_rc5 + "\x10\x77" + end),
    'unmute':   ("Turn mute off", 0, start + zone_1 + simulate_rc5 + "\x10\x78" + end)
  }, 'Power': {
    'poweron':  ("Power on", 0, start + zone_1 + simulate_rc5 + "\x10\x7b" + end),
    'poweroff': ("Power off", 0, start + zone_1 + simulate_rc5 + "\x10\x7c" + end)
  }, 'Inputs': {
    'bd':       ("Set BluRay Input", 0, start + zone_1 + simulate_rc5 + "\x10\x04" + end),
    'sat':      ("Set Sat Input", 0, start + zone_1 + simulate_rc5 + "\x10\x00" + end),
    'av':       ("Set AV Input", 0, start + zone_1 + simulate_rc5 + "\x10\x02" + end),
    'pvr':      ("Set PVR Input", 0, start + zone_1 + simulate_rc5 + "\x10\x22" + end),
    'vcr':      ("Set VCR Input", 0, start + zone_1 + simulate_rc5 + "\x10\x06" + end),
    'cd':       ("Set CD Input", 0, start + zone_1 + simulate_rc5 + "\x10\x07" + end),
    'tuner':    ("Set Tuner Input", 0, start + zone_1 + simulate_rc5 + "\x10\x03" + end),
    'net':      ("Set NET Input", 0, start + zone_1 + simulate_rc5 + "\x10\x0b" + end),
    'ipod':     ("Set iPOD Input", 0, start + zone_1 + simulate_rc5 + "\x10\x12" + end)
  }, 'Tuner Control': {
    'am':       ("Select AM", 0, start + zone_1 + simulate_rc5 + "\x11\x35" + end),
    'fm':       ("Select FM", 0, start + zone_1 + simulate_rc5 + "\x11\x34" + end),
    'net':      ("Select NET", 0, start + zone_1 + simulate_rc5 + "\x11\x7e" + end)
  }, 'Two Channel modes': {
    "directmodeon":  ("Switch to Direct Mode", 0, start + zone_1 + simulate_rc5 + "\x10\x4e" + end),
    "directmodeoff": ("Switch off Direct Mode", 0, start + zone_1 + simulate_rc5 + "\x10\x67" + end),
    "pl2movie":      ("PL II Movie", 0, start + zone_1 + simulate_rc5 + "\x10\x67" + end),
    "pl2music":      ("PL II Music", 0, start + zone_1 + simulate_rc5 + "\x10\x68" + end),
    "pl2game":       ("PL II Game", 0, start + zone_1 + simulate_rc5 + "\x10\x66" + end),
    "neo6cinema":    ("Neo 6 Cinema", 0, start + zone_1 + simulate_rc5 + "\x10\x6f" + end),
    "neo6music":     ("Neo 6 Music", 0, start + zone_1 + simulate_rc5 + "\x10\x70" + end),
    "dolbyex":       ("Dolby Ex", 0, start + zone_1 + simulate_rc5 + "\x10\x76" + end)
  }, 'Surround modes': {
    "stereo":    ("Stereo", 0, start + zone_1 + simulate_rc5 + "\x10\x6b" + end),
    "mchmode":   ("MCH Mode", 0, start + zone_1 + simulate_rc5 + "\x10\x6a" + end),
    "pl2mode":   ("PL II Mode", 0, start + zone_1 + simulate_rc5 + "\x10\x6e" + end)
  }, 'Video' : {
    "video_resolution": ("Get/Set Video Output Resolution", 1,
      lambda x : (start + zone_1 + "\x13\x01" + video_resolutions_to_num[x.lower()] + end),
      lambda x=None: x.lower() in video_resolutions_to_num if x is not None else video_resolutions_to_num.keys())
  }, 'Equalization' : {
    "treble": ("Get/Set Treble Equalisation", 1,
      lambda x : (start + zone_1 + "\x35\x01" + parse_treble(x) + end),
      check_treble),
    "bass": ("Get/Set Bass Equalisation", 1,
      lambda x : (start + zone_1 + "\x36\x01" + parse_treble(x) + end),
      check_treble),
    "room": ("Get/Set Room Equalisation", 1,
      lambda x : (start + zone_1 + "\x37\x01" + room_eq_on_off[x.lower()] + end),
      lambda x=None: x.lower() in room_eq_on_off if x is not None else room_eq_on_off.keys()),
    "dolby_volume": ("Control the status of the Dolby volume system", 1,
      lambda x : (start + zone_1 + "\x38\x01" + dolby_volume_on_off[x.lower()] + end),
      lambda x=None: x.lower() in dolby_volume_on_off if x is not None else dolby_volume_on_off.keys()),
    "dolby_leveller": ("Control the status of the leveller component of the Dolby volume system", 1,
      lambda x : (start + zone_1 + "\x39\x01" + parse_leveller[x.lower()] + end),
      check_leveller),
  }, 'Information' : {
    "help":   ("Displays this screen", 0, ""),
    "status": ("Shows Status information received", 0, "")
  }
}

answer_code = {
  0x00: "Status Update",
  0x82: "Zone Invalid",
  0x83: "Command not recognised",
  0x84: "Parameter not recognised",
  0x85: "Command invalid at this time",
  0x86: "Invalid data length"
}

responses = {
  0x00: "power",
  0x01: "display_brightness",
  0x02: "headphones_connected",
  0x03: "fm_genre",
  0x04: "version",
  0x08: "simulate_rc5",
  0x0a: "video",
  0x0b: "analogue",
  0x0c: "video_input",
  0x0d: "volume",
  0x0e: "mute",
  0x0f: "direct",
  0x10: "decode_mode_2ch",
  0x11: "decode_mode_mch",
  0x12: "rds_information",
  0x13: "video_resolution",
  0x14: "menu_status",
  0x1d: "source",
  0x35: "treble",
  0x36: "bass",
  0x37: "room",
  0x38: "dolby_volume",
  0x39: "dolby_leveller",
  0x43: "incoming_audio_format",
}

menu_status = {
  0x00: "No menu is open",
  0x02: "Set-up Menu Open",
  0x03: "Trim Menu Open",
  0x04: "Bass Menu Open",
  0x05: "Treble Menu Open",
  0x06: "Sync Menu Open",
  0x07: "Sub Menu Open",
  0x08: "Tuner Menu Open",
  0x09: "Network menu Open",
  0x0A: "iPod Menu Open",
}

decode_mode_2ch = {
  0x01: "Stereo",
  0x02: "Pro Logic II / x Movie Mode",
  0x03: "Pro Logic II / x Music Mode",
  0x04: "Pro Logic II Matrix",
  0x05: "Pro Logic II Game",
  0x06: "Dolby Pro Logic Emulation",
  0x07: "Neo:6 Cinema",
  0x08: "Neo:6 Music",
}

decode_mode_mch = {
  0x01: "Stereo down-mix",
  0x02: "Multi-channel mode",
  0x03: "Dolby EX / DTS-ES mode",
  0x04: "Pro Logic IIx movie mode",
  0x05: "Pro Logic IIx music mode",
}

display_brightness = {
  0x00: "Front panel is off",
  0x01: "Front panel L1",
  0x02: "Front panel L2",
  0x03: "Front panel L3",
}

version_software = {
  0xF0: "RS232",
  0xF1: "MCU (main)",
  0xF2: "Torino (video processor)",
  0xF3: "DSP",
  0xF4: "USB",
  0xF5: "sub MCU"
}

inc_audio_stream = {
  0x00: "PCM",
  0x01: "Analogue Direct",
  0x02: "Dolby Digital",
  0x03: "Dolby Digital EX",
  0x04: "Dolby Digital Surround",
  0x05: "Dolby Digital Plus",
  0x06: "Dolby Digital True HD",
  0x07: "DTS",
  0x08: "DTS 96/24",
  0x09: "DTS ES Matrix",
  0x0A: "DTS ES Discrete",
  0x0B: "DTS ES Matrix 96/24",
  0x0C: "DTS ES Discrete 96/24",
  0x0D: "DTS HD Master Audio",
  0x0E: "DTS HD High Res Audio",
  0x0F: "DTS Low Bit Rate",
  0x10: "DTS Core",
  0x13: "PCM Zero",
  0x14: "Unsupported",
  0x15: "Undetected",
} 

inc_audio_channel = {
  0x00: "Dual Mono",
  0x01: "Centre only",
  0x02: "Stereo only",
  0x03: "Stereo + mono surround",
  0x04: "Stereo + Surround L & R",
  0x05: "Stereo + Surround L & R + mono Surround Back",
  0x06: "Stereo + Surround L & R + Surround Back L & R",
  0x07: "Stereo + Surround L & R containing matrix information for surround back L&R",
  0x08: "Stereo + Centre",
  0x09: "Stereo + Centre + mono surround",
  0x0A: "Stereo + Centre + Surround L & R",
  0x0B: "Stereo + Centre + Surround L & R + mono Surround Back",
  0x0C: "Stereo + Centre + Surround L & R + Surround Back L & R",
  0x0D: "Stereo + Centre + Surround L & R containing matrix information for surround back L&R",
  0x0E: "Stereo Downmix Lt Rt",
  0x0F: "Stereo Only (Lo Ro)",
  0x10: "Dual Mono + LFE",
  0x11: "Centre + LFE",
  0x12: "Stereo + LFE",
  0x13: "Stereo + single surround + LFE",
  0x14: "Stereo + Surround L & R + LFE",
  0x15: "Stereo + Surround L & R + mono Surround Back + LFE",
  0x16: "Stereo + Surround L & R + Surround Back L & R + LFE",
  0x17: "Stereo + Surround L & R + LFE",
  0x18: "Stereo + Centre + LFE containing matrix information for surround back L&R",
  0x19: "Stereo + Centre + single surround + LFE",
  0x1A: "Stereo + Surround L & R + LFE (Standard 5.1)",
  0x1B: "Stereo + Centre + Surround L & R + mono Surround Back + LFE (6.1, e.g. DTS ES Discrete)",
  0x1C: "Stereo + Centre + Surround L & R + Surround Back L & R + LFE (7.1)",
  0x1D: "Stereo + Centre + Surround L & R + LFE, containing matrix information for surround back L&R (6.1 e.g. Dolby Digital EX)",
  0x1E: "Stereo Downmix (Lt Rt) + LFE",
  0x1F: "Stereo Only (Lo Ro) + LFE",
  0x20: "Unknown",
  0x21: "Undetected"
}    

video = {
  0x00: "BD",
  0x01: "SAT",
  0x02: "AV",
  0x03: "PVR",
  0x04: "VCR",
  0xF0: "Current"
}

video_input = {
  0x01: "HDMI",
  0x02: "Component",
  0x03: "S-Video",
  0x04: "CVBS",
  0xf0: "Current"
}

analogue = {
  0x00: "Use the analogue audio for the current source.",
  0x01: "Use the digital audio for the current source (if available).",
  0x02: "Use HDMI for the current source (if available).",
  0xF0: "Current",
}

source = {
  0x00: "Follow Zone 1",
  0x01: "CD",
  0x02: "BD",
  0x03: "AV",
  0x04: "SAT",
  0x05: "PVR",
  0x06: "VCR",
  0x07: "",
  0x08: "AUX",
  0x09: "DISPLAY",
  0x0A: "TUNER (AM)",
  0x0B: "TUNER (FM)",
  0x0C: "TUNER (DAB)",
  0x0D: "MCH",
  0x0E: "NET",
  0x0F: "IPOD",
}

simulate_rc5 = {
  (0x10, 0x4E): "Direct mode On",
  (0x10, 0x4F): "Direct mode Off",
  (0x10, 0x66): "PL II / IIx Game",
  (0x10, 0x41): "Frame Rate 60",
  (0x10, 0x67): "PL II / IIx Movie",
  (0x10, 0x42): "Frame Rate 'Follow Input'",
  (0x10, 0x3F): "Frame Rate Auto",
  (0x10, 0x40): "Frame Rate 50",
  (0x10, 0x68): "PL II / IIx Music", 
  (0x10, 0x1F): "Display Off",
  (0x10, 0x6A): "Multi Channel", 
  (0x10, 0x21): "Display L1",
  (0x10, 0x6B): "Stereo", 
  (0x10, 0x23): "Display L2",
  (0x10, 0x6E): "PL", 
  (0x10, 0x24): "Display L3",
  (0x10, 0x6F): "DTS Neo:6 Cinema", 
  (0x10, 0x26): "Balance left",
  (0x10, 0x70): "DTS Neo:6 Music", 
  (0x10, 0x28): "Balance right",
  (0x10, 0x76): "Dolby EX", 
  (0x10, 0x2C): "Bass +1",
  (0x10, 0x77): "Mute On", 
  (0x10, 0x2D): "Bass -1",
  (0x10, 0x78): "Mute Off", 
  (0x10, 0x2E): "Treble +1",
  (0x10, 0x35): "NET", 
  (0x10, 0x62): "Treble -1",
  (0x10, 0x36): "FM", 
  (0x17, 0x7B): "Zone 2 Power On",
  (0x10, 0x34): "AM", 
  (0x17, 0x7C): "Zone 2 Power Off",
  (0x10, 0x48): "DAB", 
  (0x17, 0x01): "Zone 2 Vol+",
  (0x10, 0x3A): "Video VCR-CVBS", 
  (0x17, 0x02): "Zone 2 Vol-",
  (0x10, 0x3C): "Video AV-CVBS", 
  (0x17, 0x03): "Zone 2 Mute",
  (0x10, 0x3E): "Video SAT-CVBS", 
  (0x17, 0x04): "Zone 2 Mute On",
  (0x10, 0x47): "Video BD-CVBS", 
  (0x17, 0x05): "Zone 2 Mute Off",
  (0x10, 0x4D): "Video VCR-Svid", 
  (0x17, 0x06): "Zone 2 CD",
  (0x10, 0x53): "Video AV-Svid", 
  (0x17, 0x07): "Zone 2 BD",
  (0x10, 0x58): "Video SAT-Svid", 
  (0x17, 0x08): "Zone 2 SAT",
  (0x10, 0x59): "Video BD-Svid", 
  (0x17, 0x09): "Zone 2 AV",
  (0x10, 0x5A): "Video VCR-HDMI", 
  (0x17, 0x0B): "Zone 2 VCR",
  (0x10, 0x5B): "Video AV-HDMI", 
  (0x17, 0x0D): "Zone 2 Aux",
  (0x10, 0x5C): "Video PVR-HDMI", 
  (0x17, 0x0E): "Zone 2 FM",
  (0x10, 0x5D): "Video SAT-HDMI", 
  (0x17, 0x0F): "Zone 2 AM",
  (0x10, 0x5E): "Video BD-HDMI", 
  (0x17, 0x10): "Zone 2 DAB",
  (0x10, 0x64): "Lip Sync +5ms", 
  (0x17, 0x12): "Zone 2 iPod",
  (0x10, 0x65): "Lip sync -5ms", 
  (0x17, 0x13): "Zone 2 NET",
  (0x10, 0x69): "Sub trim +0.5dB", 
  (0x10, 0x6C): "Sub trim -0.5dB", 
  (0x10, 0x6D): "PLII Music Centre +1", 
  (0x10, 0x71): "PLII Music Centre -1", 
  (0x10, 0x72): "PLII Music Dimension +1", 
  (0x10, 0x73): "PLII Music Dimension -1", 
  (0x10, 0x74): "PLII Panorama On", 
  (0x10, 0x75): "PLII Panorama Off", 
  (0x10, 0x7D): "Video out Preferred/Best", 
  (0x10, 0x0F): "Video out SD Prog", 
  (0x10, 0x17): "Video out 720p", 
  (0x10, 0x1A): "Video out 1080i", 
  (0x10, 0x1B): "Video out 1080p", 
  (0x10, 0x1C): "Video out Bypass",
  (0x11, 0x01): "Numeric entry - 1",
  (0x11, 0x02): "Numeric entry - 2",
  (0x11, 0x03): "Numeric entry - 3",
  (0x11, 0x04): "Numeric entry - 4",
  (0x10, 0x04): "Select BD",
  (0x11, 0x05): "Numeric entry - 5",
  (0x10, 0x05): "Select Display (Audio Return Channel)",
  (0x11, 0x06): "Numeric entry - 6",
  (0x10, 0x03): "Select Tuner",
  (0x11, 0x07): "Numeric entry - 7",
  (0x11, 0x08): "Numeric entry - 8",
  (0x10, 0x0C): "Standby",
  (0x10, 0x01): "Select Phono",
  (0x10, 0x02): "Select AV",
  (0x10, 0x06): "Select VCR",
  (0x10, 0x07): "Select CD",
  (0x10, 0x08): "Select Aux",
  (0x11, 0x09): "Numeric entry - 9",
  (0x10, 0x09): "Select MCH",
  (0x11, 0x00): "Numeric entry - 0",
  (0x10, 0x00): "Select SAT",
  (0x11, 0x56): "Navigate Up / Increment Preset",
  (0x10, 0x22): "Select PVR",
  (0x11, 0x4E): "Navigate Left / Decrease Tuning",
  (0x10, 0x30): "Random",
  (0x11, 0x57): "OK / SELECT",
  (0x10, 0x31): "Repeat",
  (0x11, 0x4D): "Navigate Right / Increase Tuning",
  (0x11, 0x55): "Navigate Down / Decrement Preset",
  (0x10, 0x12): "Select iPod",
  (0x10, 0x0B): "Select NET",
  (0x11, 0x32): "BAND",
  (0x10, 0x56): "Navigate Up",
  (0x11, 0x7D): "MENU",
  (0x10, 0x51): "Navigate Left",
  (0x11, 0x12): "Change VFD Brightness (DISP)",
  (0x10, 0x57): "OK",
  (0x11, 0x21): "Preset - (CH- / track back symbol)",
  (0x10, 0x50): "Navigate Right",
  (0x11, 0x20): "Preset + (CH+ / track fwd symbol)",
  (0x10, 0x55): "Navigate Down",
  (0x11, 0x35): "Select AM",
  (0x10, 0x20): "Cycle between decoding modes (MODE)",
  (0x11, 0x34): "Select FM",
  (0x10, 0x52): "Enter system menu (MENU)",
  (0x11, 0x7F): "Select FM",
  (0x11, 0x7E): "Select DAB",
  (0x10, 0x0D): "Mute",
  (0x10, 0x3B): "Change VFD brightness (DISP)",
  (0x11, 0x26): "Page Up (preset list)",
  (0x10, 0x11): "Decrease volume (-)",
  (0x11, 0x25): "Page Down (preset list)",
  (0x10, 0x10): "Increase volume (+)",
  (0x11, 0x29): "Delete selected preset",
  (0x11, 0x0F): "Cycle between VFD information panels",
  (0x10, 0x39): "CH- (track back symbol)",
  (0x10, 0x38): "CH+ (track fwd symbol)",
  (0x10, 0x0A): "Activate DIRECT mode",
  (0x10, 0x1E): "Room EQ on/off / NET 'Now Playing' screen / IPOD Play/Pause",
  (0x10, 0x46): "Toggle Dolby Volume on/off / NET & IPOD Play/Pause",
  (0x10, 0x27): "Access Bass control",
  (0x10, 0x25): "Access Speaker Trim controls",
  (0x10, 0x32): "Access Lipsync Delay control / NET & IPOD Stop",
  (0x10, 0x33): "Access Subwoofer Trim control",
  (0x10, 0x0E): "Access Treble control",
  (0x10, 0x29): "FAV+ / red / Page Up",
  (0x10, 0x2A): "FAV- / green / Page Down",
  (0x10, 0x2B): "HOME / yellow",
  (0x10, 0x37): "Cycle between VFD information panels / blue",
  (0x10, 0x5F): "Change control to next zone",
  (0x10, 0x14): "Set selected zone to Follow Zone 1",
  (0x10, 0x2F): "Cycle between output resolutons",
  (0x10, 0x13): "Cycle between aspect ratios (Auto, 16:9, 4:3)",
  (0x10, 0x7B): "Power On",
  (0x10, 0x7C): "Power Off",
}
