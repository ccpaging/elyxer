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
# Alex 20091214
# eLyXer functions with a variable number of parameters.

import sys
from gen.container import *
from util.trace import Trace
from conf.config import *
from math.bits import *
from math.command import *


class HybridFunction(CommandBit):
  "Read a function with two parameters: [] and {}"
  "The [] parameter is optional"

  commandmap = FormulaConfig.hybridfunctions
  parambrackets = [('[', ']'), ('{', '}')]

  def parsebit(self, pos):
    "Parse a function with [] and {} parameters"
    readtemplate = self.translated[0]
    writetemplate = self.translated[1]
    params = self.readparams(readtemplate, pos)
    self.contents = self.writeparams(params, writetemplate)

  def readparams(self, readtemplate, pos):
    "Read the params according to the template."
    params = dict()
    for paramdef in self.paramdefs(readtemplate):
      if paramdef.startswith('['):
        value = self.parsesquare(pos)
      elif paramdef.startswith('{'):
        value = self.parseparameter(pos)
      else:
        Trace.error('Invalid parameter definition ' + paramdef)
        value = None
      params[paramdef[1:-1]] = value
    return params

  def paramdefs(self, readtemplate):
    "Read each param definition in the template"
    pos = Position().withtext(readtemplate)
    while not pos.finished():
      paramdef = self.readparamdef(pos)
      if paramdef:
        if len(paramdef) != 4:
          Trace.error('Parameter definition ' + paramdef + ' has wrong length')
        else:
          yield paramdef

  def readparamdef(self, pos):
    "Read a single parameter definition: [$0], {$x}..."
    for (opening, closing) in HybridFunction.parambrackets:
      if pos.checkskip(opening):
        if not pos.checkfor('$'):
          Trace.error('Wrong parameter name ' + pos.current())
          return None
        return opening + pos.globincluding(closing)
    Trace.error('Wrong character in parameter template' + pos.currentskip())
    return None

  def writeparams(self, params, writetemplate):
    "Write all params according to the template"
    return self.writepos(params, Position().withtext(writetemplate))

  def writepos(self, params, pos):
    "Write all params as read in the parse position."
    result = []
    while not pos.finished():
      if pos.checkskip('$'):
        param = self.writeparam(params, pos)
        if param:
          result.append(param)
      elif pos.checkskip('f'):
        function = self.writefunction(params, pos)
        if function:
          result.append(function)
      else:
        result.append(FormulaConstant(pos.currentskip()))
    return result

  def writeparam(self, params, pos):
    "Write a single param of the form $0, $x..."
    name = '$' + pos.currentskip()
    if not name in params:
      Trace.error('Unknown parameter ' + name)
      return None
    if not params[name]:
      return None
    if pos.checkskip('.'):
      params[name].type = pos.globalpha()
    return params[name]

  def writefunction(self, params, pos):
    "Write a single function f0,...,fn."
    tag = self.readtag(params, pos)
    if not tag:
      return None
    if not pos.checkskip('{'):
      Trace.error('Function should be defined in {}')
      return None
    pos.pushending('}')
    contents = self.writepos(params, pos)
    pos.popending()
    if len(contents) == 0:
      return None
    function = TaggedBit().complete(contents, tag)
    function.type = None
    return function

  def readtag(self, params, pos):
    "Get the tag corresponding to the given index. Does parameter substitution."
    if not pos.current().isdigit():
      Trace.error('Function should be f0,...,f9: f' + pos.current())
      return None
    index = int(pos.currentskip())
    if 2 + index > len(self.translated):
      Trace.error('Function f' + unicode(index) + ' is not defined')
      return None
    tag = self.translated[2 + index]
    if not '$' in tag:
      return tag
    for name in params:
      if name in tag:
        if params[name]:
          value = params[name].original[1:-1]
        else:
          value = ''
        tag = tag.replace(name, value)
    return tag

FormulaCommand.commandbits += [
    HybridFunction(),
    ]
