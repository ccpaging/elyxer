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
# Alex 20090207
# eLyXer tables

from util.trace import Trace
from gen.container import *
from io.parse import *
from io.output import *


class Table(Container):
  "A lyx table"

  start = '\\begin_inset Tabular'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TaggedOutput().settag('table', True)

class TableHeader(Container):
  "The headers for the table"

  starts = ['<lyxtabular', '<features', '<column', '</lyxtabular']

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

class Row(Container):
  "A row in a table"

  start = '<row'
  ending = '</row'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TaggedOutput().settag('tr', True)

  def process(self):
    if len(self.header) > 1:
      self.output.tag += ' class="header"'

class Cell(Container):
  "A cell in a table"

  start = '<cell'
  ending = '</cell'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TaggedOutput().settag('td', True)

ContainerFactory.types += [Table, TableHeader, Row, Cell]
