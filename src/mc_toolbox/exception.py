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
    'UtilsError',
    'NotAMacOS',
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

# utils.py
class UtilsError(Error): pass
class NotAMacOS(UtilsError): pass
