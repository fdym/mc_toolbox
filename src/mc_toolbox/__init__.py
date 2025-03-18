# -*- coding: utf-8 -*-
#
#  __init__.py
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
from . import (
    cache,
    download,
    download_manager,
    download_manager_legacy,
    exception,
    futures,
    java,
    launch,
    resources,
    source,
    utils,
)

__all__ = [
    'cache',
    'download',
    'download_manager',
    'download_manager_legacy',
    'exception',
    'futures',
    'java',
    'launch',
    'resources',
    'source',
    'utils',
]
__author__ = [
    'fdym <fdym_dlygzh@163.com>',
]
__version__ = '0.3'