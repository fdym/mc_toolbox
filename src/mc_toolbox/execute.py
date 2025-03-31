# -*- coding: utf-8 -*-
#
#  execute.py
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
Execute the program and monitor its output.
'''
from collections import namedtuple
from logging import FATAL, ERROR, WARNING, INFO, DEBUG, NOTSET as TRACE
from os.path import dirname
from subprocess import Popen, STDOUT
from tempfile import NamedTemporaryFile
from typing import Callable, List, Optional
import re

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

__all__ = [
    'ExecuteNamedTuple',
    'MINECRAFT_LOGGER',
    'MINECRAFT_LOGGER_CATEGORY',
    'level_strings',
    'guess_level',
    'simple_callback',
    'start',
]

ExecuteNamedTuple = namedtuple('ExecuteNamedTuple', ['pipe', 'observer', 'temp'])

MINECRAFT_LOGGER = re.compile('\\[(?P<timestamp>[0-9:]+)] \\[[^/]+/(?P<level>[^]]+)]')
MINECRAFT_LOGGER_CATEGORY = re.compile('\\[(?P<timestamp>[0-9:]+)] \\[[^/]+/(?P<level>[^]]+)] \\[(?P<category>[^]]+)]')

level_strings = {
    FATAL: 'FATAL',
    ERROR: 'ERROR',
    WARNING: 'WARNING',
    INFO: 'INFO',
    DEBUG: 'DEBUG',
    TRACE: 'TRACE',
}

def guess_level(line: str) -> int:
    '''
    Guess the log level of a certain line.
    '''
    level = INFO
    m = MINECRAFT_LOGGER.match(line)
    if m:
        level_str = m.group('level')
        if level_str == 'TRACE':
            level = TRACE
        elif level_str == 'DEBUG':
            level = DEBUG
        elif level_str == 'INFO':
            level = INFO
        elif level_str == 'WARN':
            level = WARNING
        elif level_str == 'ERROR':
            level = ERROR
        elif level_str == 'FATAL':
            level = FATAL
        
        m2 = MINECRAFT_LOGGER_CATEGORY.match(line)
        if m2:
            level_str2 = m2.group('category')
            if level_str2 == 'STDOUT':
                level = INFO
            elif level_str2 == 'STDERR':
                level = ERROR
    else:
        if (
            ('[INFO]' in line) 
            or ('[CONFIG]' in line)
            or ('[FINE]' in line)
            or ('[FINER]' in line)
            or ('[FINEST]' in line)
        ):
            level = INFO
        if (
            ('[SEVERE]' in line) 
            or ('[STDERR]' in line)
        ):
            level = ERROR
        if '[WARNING]' in line:
            level = WARNING
        if '[DEBUG]' in line:
            level = DEBUG
    if 'overwriting existing' in line:
        level = FATAL
    return level

def simple_callback(lines: List[str]):
    for line in lines:
        level = guess_level(line)
        print('{level} {line}'.format(level=level_strings[level], line=line), end='')

class _PathEventHandler(FileSystemEventHandler):
    def __init__(self, path: str, callback: Callable[[List[str]], None]):
        self.path = path
        self.callback = callback
        self._last_pos = 0

    def on_modified(self, event: FileSystemEvent):
        if event.src_path == self.path:
            with open(self.path, buffering=1, encoding='utf-8') as f:
                f.seek(self._last_pos)
                lines = f.readlines()
                self._last_pos = f.tell()
                if lines:
                    self.callback(lines)

def start(arg: str, log: bool=True, callback: Optional[Callable[[List[str]], None]]=simple_callback) -> ExecuteNamedTuple[Popen, Optional[Observer]]:
    '''
    Execute commands and monitor their output.

    arg: command
    log: represents whether to track the output Boolean value
    callback: if log is True, the monitored output lines will be passed to this parameter in a list format
    
    If the log is False, the observer item of the return value will be None.
    '''
    temp = NamedTemporaryFile('w+', buffering=1, encoding='utf-8', delete=False)
    pipe = Popen(
        arg,
        bufsize=1,
        stdout=temp,
        stderr=STDOUT,
        shell=True,
        encoding='utf-8',
    )
    observer = None
    if log:
        handler = _PathEventHandler(temp.name, callback)
        observer = Observer()
        observer.schedule(handler, path=dirname(temp.name))
        observer.start()
    return ExecuteNamedTuple(pipe, observer, temp)
