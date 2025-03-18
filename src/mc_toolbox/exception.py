# -*- coding: utf-8 -*-
#
#  exception.py
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
__all__ = [
    'Error',
    'DownloadError',
    'DisableHttps',
    'RequestFailure',
    'DownloadErrorS',
    'ManagerError',
    'DatabaseError',
    # 'JavaError',
    # 'NotSupported',
    'SourceError',
    'MinecraftVersionNotFound',
    # 'LiteLoaderVersionNotFound',
    'OptiFineVersionNotFound',
]

class Error(Exception): pass

# download.py
class DownloadError(Error): pass
class DisableHttps(DownloadError): pass
class RequestFailure(DownloadError): pass
class DownloadErrorS(DownloadError): pass

# download_manager.py
class ManagerError(Error): pass
class DatabaseError(ManagerError): pass

# # java.py
# class JavaError(Error): pass
# class NotSupported(JavaError): pass

# source.py
class SourceError(Error): pass
class MinecraftVersionNotFound(SourceError): pass
# class LiteLoaderVersionNotFound(SourceError): pass
class OptiFineVersionNotFound(SourceError): pass
