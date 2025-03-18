# -*- coding: utf-8 -*-
#
#  utils.py
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
This module provides some practical tools (such as detecting operating systems, etc.).
'''
from enum import Enum
from subprocess import PIPE, Popen
import platform as pf
import re

__all__ = [
    'Platform',
    'Arch',
    'get_platform',
    'get_architecture',
    'get_system_version',
    'VANILLA',
    'FORGE',
    'FABRIC',
    # 'LITELOADER'
    'QUILT',
    'NEOFORGE',
    'OPTIFINE',
    'MICROSOFT',
    'OFFLINE',
]

# platform
class Platform(Enum):
    LINUX = 0 # glibc
    ALPINE_LINUX = 1 # musl libc
    MACOS = 2
    WINDOWS = 3

# architecture
class Arch(Enum):
    X64 = 0
    X86 = 1
    ARM64 = 2
    ARM_HF = 3 # hardware floating point
    ARM_EL = 4 # no hardware floating point

def get_platform(is_glibc=True):
    if pf.system() == 'Windows':
        return Platform.WINDOWS
    elif pf.system() == 'Darwin':
        return Platform.MACOS
    elif pf.system() == 'Linux':
        return Platform.LINUX if is_glibc else Platform.ALPINE_LINUX

def get_architecture(hf=True):
    arch = pf.uname().machine.replace('-', '_').lower()
    if arch in ['x86', 'x86_32', 'x32', 'ia32', 'i386', 'i486', 'i586', 'i686', 'i86pc']:
        return Arch.X86
    elif arch in ['x64', 'x86_64', 'amd64', 'em64t']:
        return Arch.X64
    elif (arch in ['arm64', 'aarch64']) or ('armv8' in arch) or ('armv9' in arch):
        return Arch.ARM64
    elif (arch in ['arm', 'arm32', 'aarch32']) or ('armv' in arch):
        return Arch.ARM_HF if hf else Arch.ARM_EL

def get_system_version() -> str:
    if get_platform() == Platform.MACOS:
        p = Popen("sw_vers", stdout=PIPE)
        result = p.communicate()[0].decode('ascii')
        ver = re.compile(r'ProductVersion:\s(.*)').search(result).group(1)
        return ver
    if get_platform() == Platform.WINDOWS:
        return pf.version()

VANILLA = 'Minecraft'
FORGE = 'Forge'
FABRIC = 'Fabric'
# LITELOADER = 'LiteLoader'
QUILT = 'Quilt'
NEOFORGE = 'Neoforge'
OPTIFINE = 'OptiFine'

MICROSOFT = 'msa'
OFFLINE = 'legacy'
