#! /usr/bin/env python
# -*- coding: utf-8 -*-

#   eLyXer -- convert LyX source files to HTML output.
#
#   Copyright (C) 2009 Alex Fernández
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

# --end--
# Alex 20090203
# eLyXer parsers

import datetime
from elyxer.util.trace import Trace
from elyxer.io.fileline import *


class ConfigReader(object):
  "Read a configuration file"

  escapes = [
      ('\n', '&#10;'), (':', '&#58;'), ('#', '&#35;'),
      ('[', '&#91;'), (']', '&#93;'), ('&', '&#38;'),
      ]

  def __init__(self, filename):
    self.reader = LineReader(filename)
    self.objects = dict()
    self.section = None
    self.serializer = ConfigSerializer(ConfigReader.escapes)

  def parse(self):
    "Parse the whole file"
    while not self.reader.finished():
      self.parseline(self.reader.currentline())
      self.reader.nextline()
    return self

  def parseline(self, line):
    "Parse a single line"
    if line == '':
      return
    if line.startswith('#'):
      return
    if line.startswith('['):
      self.parsesection(line)
    else:
      self.parseparam(line)

  def parsesection(self, line):
    "Parse a section header"
    if not line.endswith(']'):
      Trace.error('Incorrect section header ' + line)
      return
    name = line[1:-1]
    self.section = name
    self.objects[name] = dict()

  def parseparam(self, line):
    "Parse a parameter line"
    if len(line.strip()) == 0:
      return
    if not ':' in line:
      Trace.error('Invalid configuration parameter ' + line)
      return
    pieces = line.split(':', 1)
    key = self.serializer.unescape(pieces[0])
    value = self.serializer.deserialize(pieces[1])
    object = self.objects[self.section]
    if key in object:
      Trace.error('Repeated key ' + key + ' for ' + value)
    object[key] = value

class ConfigWriter(object):
  "Write a configuration file"

  def __init__(self, writer):
    self.writer = writer
    self.serializer = ConfigSerializer(ConfigReader.escapes)

  def writeall(self, types):
    "Write a list of configuration objects given their class names"
    for type in types:
      object = type.__new__(type)
      self.write(object)

  def write(self, object):
    "Write a configuration object"
    for attr in dir(object):
      self.writeattr(object, attr)

  def writeattr(self, object, attr):
    "Write an attribute"
    if attr.startswith('__'):
      return
    self.writesection(object, attr)
    valuedict = getattr(object, attr)
    if not isinstance(valuedict, dict):
      Trace.error('Unknown config type ' + valuedict.__class__.__name__ +
          ' in ' + attr)
      return
    names = list(valuedict.keys())
    names.sort()
    for name in names:
      value = self.serializer.serialize(valuedict[name])
      self.writer.writeline(self.serializer.escape(name) + ':' + value)

  def writesection(self, object, attr):
    "Write a new section"
    self.writer.writeline('')
    header = '[' + object.__class__.__name__ + '.' + attr + ']'
    self.writer.writeline(header)

class ConfigToPython(ConfigWriter):
  "Exports a number of dictionaries from elyxer.a config file to a Python class"

  escapes = [ ('\\', '\\\\'), ('\n', '\\n'), ('\'', '\\\'') ]

  def __init__(self, writer):
    self.writer = writer
    self.serializer = ConfigSerializer(ConfigToPython.escapes)

  def write(self, objects):
    "Write the whole set of objects"
    self.writer.writeline('#! /usr/bin/env python')
    self.writer.writeline('# -*- coding: utf-8 -*-')
    self.writer.writeline('')
    self.writer.writeline('# eLyXer configuration')
    self.writer.writeline('# autogenerated from elyxer.config file on ' +
        datetime.date.today().isoformat())
    self.writer.writeline('')
    classes = self.sort(objects)
    names = list(classes.keys())
    names.sort()
    for classname in names:
      self.writeclass(classname, classes[classname])

  def writeclass(self, name, current):
    "Write an object class"
    self.writer.writeline('class ' + name + '(object):')
    self.writer.writeline('  "Configuration class from elyxer.config file"')
    self.writer.writeline('')
    names = list(current.keys())
    names.sort()
    for attrname in names:
      self.writeattr(attrname, current[attrname])

  def writeattr(self, name, contents):
    "Write a dictionary attribute"
    if not isinstance(contents, dict):
      Trace.error('Unknown config type ' + contents.__class__.__name__)
      return
    self.writer.writestring('  ' + name + ' = ')
    self.writer.writeline('{')
    string = '      '
    names = list(contents.keys())
    names.sort()
    for name in names:
      value = self.serializer.pyserialize(contents[name])
      piece = '\'' + self.serializer.escape(name) + '\':' + value + ', '
      string = self.append(string, piece)
    self.writer.writeline(string)
    self.writer.writeline('      }')
    self.writer.writeline('')

  def append(self, string, piece):
    "Write a piece to the string or to disk"
    if len(string + piece) > 80:
      self.writer.writeline(string)
      string = '      '
    return string + piece

  def sort(self, objects):
    "Sort the objects into classes"
    classes = dict()
    for name, object in objects.items():
      pieces = name.split('.')
      if len(pieces) != 2:
        Trace.error('Wrong method name ' + name)
        return
      classname = pieces[0]
      methodname = pieces[1]
      if not classname in classes:
        classes[classname] = dict()
      currentclass = classes[classname]
      currentclass[methodname] = object
    return classes

class ConfigSerializer(object):
  "Serialize and deserialize config object"

  def __init__(self, escapes):
    self.escapes = escapes

  def serialize(self, object):
    "Convert an object to a string"
    if not isinstance(object, list):
      return self.escape(object)
    result = ''
    for value in object:
      result += self.escape(value) + ','
    if len(object) > 0:
      result = result[:-1]
    return '[' + result + ']'

  def pyserialize(self, object):
    "Convert an object to a Python definition"
    if not isinstance(object, list):
      return '\'' + self.escape(object) + '\''
    result = '[\''
    for value in object:
      result += self.escape(value) + '\',\''
    if len(object) > 0:
      result = result[:-2]
    return result + ']'

  def escape(self, string):
    "Escape a string or a list"
    for escape, value in self.escapes:
      if escape in string:
        string = string.replace(escape, value)
    return string

  def deserialize(self, string):
    "Parse a string into an object (string or list)"
    if not string.startswith('[') or not string.endswith(']'):
      return self.unescape(string)
    result = []
    contents = string[1:-1].split(',')
    for piece in contents:
      result.append(self.unescape(piece))
    return result

  def unescape(self, string):
    "Remove the escaping from elyxer.a string."
    if string.startswith('&#x') and string.endswith(';'):
      # single unicode character
      return chr(int('0x' + string[3:-1], 16))
    for escape, value in self.escapes:
      string = string.replace(value, escape)
    return string

