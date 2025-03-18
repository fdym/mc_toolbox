# -*- coding: utf-8 -*-
#
#  java.py
#  
#  Copyright 2025 fdym
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
'''
This module provides various tools related to Java.
'''
from .utils import Arch

class Java:
    def __init__(self, path: str, version: str, arch: Arch):
        self._path = path
        self._version = version
        self._arch = arch

    @property
    def path(self):
        return self._path

    @property
    def version(self):
        return self._version
    
    @property
    def arch(self):
        return self._arch
    
    @property
    def major_version(self) -> int:
        if int(self.version.split('.')[0])== 1: # 1.8, 1.7, ...
            return int(self.version.split('.')[1])
        else:
            return int(self.version.split('.')[0])

    @property
    def json(self):
        return {"path": self.path, "version": self.version}

    def __hash__(self):
        return hash((self._path, self._version))

    def __str__(self):
        return f'<Java {repr(self.json)}>'

    def __eq__(self, other):
        if isinstance(other, Java):
            return self._path == other._path and self._version == other._version
