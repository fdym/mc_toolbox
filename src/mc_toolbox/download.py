# -*- coding: utf-8 -*-
#
#  download.py
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
This module provides multiple ways to download single or multiple files.
'''
from io import BytesIO
from os import remove, rename
from os.path import exists
from queue import Queue
from sys import exc_info
from tempfile import TemporaryFile
from time import sleep
from typing import List, IO, Union, Optional
from urllib.parse import urlparse
import logging
import threading

from requests.exceptions import Timeout
from requests.sessions import Session
import requests

from .exception import DisableHttps, RequestFailure, DownloadErrorS
from .utils import get_platform, Platform

__all__ = [
    'rename_if_exist',
    'remove_if_exist',
    'raise_if_exist',
    'HttpProxy',
    'SocksProxy',
    'NoProxy',
    'Downloader',
    'MultithreadingDownloader',
    'download',
    'multithreading_downloadS',
    'multithreading_download',
]

logger = logging.getLogger(__name__)

def rename_if_exist(filename: str):
    '''
    Resolve the issue of duplicate files by renaming them.
    '''
    s = '\\' if get_platform() == Platform.WINDOWS else '/'
    filename_nopath = filename.split(s)[-1]
    path = s.join(filename.split(s)[:-1])
    path = path + s if path != '' else path
    if exists(filename):
        l = filename_nopath.split('.')
        l[0] += '({})'
        result = '.'.join(l)
        i = 1
        while exists(path + result.format(i)):
            i += 1
        return path + result.format(i)
    return filename

def remove_if_exist(filename: str):
    '''
    Resolve the issue of duplicate files by deleting the original files.
    '''
    try:
        remove(filename)
    except FileNotFoundError: pass
    return filename

def raise_if_exist(filename: str):
    '''
    Resolve the issue of duplicate files by throwing FileExistsError.
    '''
    if exists(filename):
        raise FileExistsError(f'{filename} is exists.')
    return filename

class HttpProxy:
    '''
    Describe the class of HTTP proxies.

    :param netloc: URL withOUT protocol
    :param https: boolean representing whether HTTPS is used or not
    :param username: proxy username
    :param password: proxy password

    example:
    `proxy = HttpProxy('142.8.5.7:8080', True, 'username', 'password'`
    '''
    def __init__(
        self, netloc: str, https=False,
        username: str=None, password: str=None
    ):
        self.netloc = netloc
        self.https = https
        self.username = username
        self.password = password

    def __str__(self):
        return f'<HttpProxy {self.netloc}>'

    @property
    def value(self):
        if self.username:
            return f'http://{self.username}:{self.password}@{self.netloc}'
        else:
            return f'http://{self.netloc}'

    @property
    def value_https(self):
        if not self.https:
            raise DisableHttps('HTTPS is disable.')
        if self.username:
            return f'https://{self.username}:{self.password}@{self.netloc}'
        else:
            return f'https://{self.netloc}'

    @property
    def proxies(self):
        proxies = {
            'http': self.value
        }
        if self.https:
            proxies['https'] = self.value_https
        return proxies

class SocksProxy:
    '''
    Describe the class of HTTP proxies

    :param netloc: URL withOUT protocol
    :param username: proxy username
    :param password: proxy password

    example:
    `proxy = SocksProxy('142.8.5.7:8080', 'username', 'password')`
    '''
    def __init__(self, netloc: str, username: str=None, password: str=None):
        self.netloc = netloc
        self.username = username
        self.password = password

    def __str__(self):
        return f'<SocksProxy {self.netloc}>'

    @property
    def value(self):
        if self.username:
            return f'socks://{self.username}:{self.password}@{self.netloc}'
        else:
            return f'socks://{self.netloc}'

    @property
    def proxies(self):
        proxies = {
            'http': self.value,
            'https': self.value
        }
        return proxies

class NoProxy:
    proxies = None
    
    @staticmethod
    def __bool__(): return False

    def __str__(self):
        return '<NoProxy>'

class FakeResponse:
    ok = False
    status_code = 408

    @staticmethod
    def __bool__(): return False

class Downloader:
    '''
    A regular file download class.

    :param url: the URL of the file that needs to be downloaded
    :param file: file path (can be a relative path)
    :param proxies: HTTP/SOCKS proxy object, default value is an instance of NoProxy (indicating not using a proxy)
    :param timeout: how long to wait is considered timeout, default is None
    :param retry: the number of retries after a failed request, default is 0
    :param headers: request header, default value is {}
    :param chunk_size:  unit for streaming download, default 8KB
    :param when_exist:  a function used to handle files with duplicate names.
                 When used, it passes a parameter representing the original file name and should return the processed file name.
                 The default value is rename_if_exist

    Note: Excessive retry can lead to RecursiveError
    '''
    def __init__(self,
            url: str, filename: str,
            proxies: Union[HttpProxy, SocksProxy, NoProxy]=NoProxy(), timeout: float=None, retry: int=0, headers: dict={},
            chunk_size: int=1024 * 8, when_exist=rename_if_exist
    ):
        self.url = url
        self.filename = filename
        self.proxies = proxies
        self.timeout = timeout
        self.retry = retry
        self.headers = headers
        self.chunk_size = chunk_size
        self.when_exist = when_exist

        self.__stop = False
        self.__pause = False

        logger.info(f'Initialize a {self.__class__.__name__} instance. (from {url} to {filename})')

    def pause(self):
        '''
        Pause download, but data will be retained.
        '''
        self.__pause = True
        logger.info(f'Pause a {self.__class__.__name__} from {self.url} to {self.filename}.')
        return self

    def unpause(self):
        '''
        Unpause download, this will continue downloading from where it was interrupted.
        '''
        self.__pause = False
        logger.info(f'Unpause a {self.__class__.__name__} from {self.url} to {self.filename}.')
        return self

    @property
    def is_pause(self): return self.__pause

    @property
    def is_stop(self): return self.__stop

    def start(self, retry: int=None):
        '''
        Start downloading.
        This method is very suitable for using concurrent.futures.ProcessPoolExecutor to execute.
        '''
        self.__stop = False
        self.__pause = False
        self.filename = self.when_exist(self.filename)
        logger.info(f'{self.__class__.__name__} from {self.url} to {self.filename} has started, remaining retry attempts: {retry if retry else self.retry}.')
        temporary_file_name = self.filename + '.download'
        try:
            response = requests.get(self.url, stream=True, proxies=self.proxies.proxies, timeout=self.timeout, headers=self.headers)
        except Timeout:
            response = FakeResponse()
            logger.warning(f'The request for {self.url} has timed out.')
        if response.ok:
            f = open(temporary_file_name, 'wb')
            for chunk in response.iter_content(self.chunk_size): # Streaming download
                if self.is_stop: # stop
                    f.close()
                    remove(temporary_file_name)
                    return self
                while self.is_pause: # pause
                    sleep(0.01)
                f.write(chunk)
            f.close()
            rename(temporary_file_name, self.filename)
        else:
            if retry != 0:
                # Implementing retry logic through recursion
                logger.error(f'Request failure. status_code={response.status_code}. Try again.')
                if retry:
                    self.start(retry - 1)
                else:
                    self.start(self.retry - 1)
            else:
                logger.error(f'Request failure. status_code={response.status_code}.')
                raise RequestFailure(f'Request failure. status_code={response.status_code}')
        logger.info(f'Successfully downloaded from {self.url} to {self.filename}.')
        return self

    def fake_start(self):
        '''
        Only set the stop property to False and do not download.
        '''
        self.__stop = False
        return self

    def stop(self):
        '''
        Stop downloading and delete files caused by downloading.
        '''
        self.__stop = True
        logger.info(f'Stop a {self.__class__.__name__} from {self.url} to {self.filename}.')
        return self

    run = start

class MultithreadingDownloader(Downloader):
    '''
    A class that accelerates downloading by simultaneously downloading multiple parts of a single file through thread based parallelism.

    :param url: the URL of the file that needs to be downloaded
    :param file: file path (can be a relative path)
    :param proxies: HTTP/SOCKS proxy object, default value is an instance of NoProxy (indicating not using a proxy)
    :param timeout: how long to wait is considered timeout, default is None
    :param retry: the number of retries after a failed request, default is 0
    :param headers: request header, default value is {}
    :param num_threads: number of threads, default is 60
    :param chunk_size:  unit for streaming download, default 8KB
    :param thread_timeout: same as timeout, but used to wait for threads
    :param in_memory:  whether to use memory to store temporary data, default is False
    :param when_exist:  a function used to handle files with duplicate names.
                        When used, it passes a parameter representing the original file name and should return the processed file name.
                        The default value is rename_if_exist

    Note: 
    Excessive retry can lead to RecursiveError;
    If the downloaded file is not a binary file or the file size is less than 1MB, the download() function will be called directly
    '''
    single_threading_downloader = Downloader

    def __init__(self,
            url: str, filename: str,
            proxies: Union[HttpProxy, SocksProxy, NoProxy]=NoProxy(), timeout: float=None, retry: int=0, headers: dict={},
            num_threads: int=60, in_memory=False, thread_timeout: float= None,
            chunk_size: int=1024 * 8, when_exist=rename_if_exist
    ):
        super().__init__(url, filename, proxies, timeout, retry, headers, chunk_size, when_exist)
        self.num_threads = num_threads
        self.in_memory = in_memory
        self.thread_timeout = thread_timeout

        # Declare its existence
        self.__stop = False
        self.__pause = False

    def start(self, retry: int=None):
        '''
        Start downloading.
        This method is very suitable for using concurrent.futures.ProcessPoolExecutor to execute.
        '''
        self.__stop = False
        self.__pause = False
        self.filename = self.when_exist(self.filename)
        logger.info(f'{self.__class__.__name__} from {self.url} to {self.filename} has started, remaining retry attempts: {retry if retry else self.retry}.')
        session = Session()
        temporary_file_name = self.filename + '.download'

        resp_headers = session.head(
            self.url, proxies=self.proxies.proxies, headers=self.headers, allow_redirects=True
        ).headers
        size = int(resp_headers.get('Content-Length', 0)) # Note: The response header of the text file does not have "Content-Length"
        accept_ranges = resp_headers.get('Accept-Ranges', None)
        logger.debug(f'The size of {self.url} is {size}.')
        if size < 1024 * 1024: # 1 MB
            logger.warning(f'The size of {self.url} is less than 1MB or it is a text file. Do not use multi-threaded downloads.')
            return self.single_threading_downloader(
                self.url,
                self.filename,
                self.proxies,
                self.timeout,
                self.retry,
                self.headers,
                self.chunk_size,
                self.when_exist,
            )
        elif accept_ranges == None:
            logger.warning(f'"{urlparse(self.url).netloc}" does not support Range.')
            return self.single_threading_downloader(
                self.url,
                self.filename,
                self.proxies,
                self.timeout,
                self.retry,
                self.headers,
                self.chunk_size,
                self.when_exist,
            )
        else:
            error_queue = Queue()
            # Using temporary files to avoid excessive memory consumption,
            # or using memory to increase read and write performance
            temps = [(BytesIO if self.in_memory else TemporaryFile)() for i in range(self.num_threads)]
            ranges = [(i * (size // self.num_threads), (i + 1) * (size // self.num_threads) - 1) for i in range(self.num_threads)]
            ranges[-1] = (ranges[-1][0], None)

        def download_in_thread(file: IO, retry: int=0, start: int=0, end: Optional[int]=None):
            logger.info(f'A thread starts downloading the range ({start}-{end if end else ""}) of {self.url}, with a remaining retry count of {retry if retry else self.retry}.')
            file.seek(0)
            try:
                try:
                    # If the value of Range is "bytes=<start>-", it will be downloaded from<start>all the way to the end of the file
                    updated_headers = {'Range': f'bytes={start}-{end if end else ""}'}
                    updated_headers.update(self.headers)
                    response = session.get(self.url, stream=True, proxies=self.proxies.proxies, timeout=self.timeout, headers = updated_headers, allow_redirects=True)
                except Timeout:
                    response = FakeResponse()
                    logger.warning(f'The request for {self.url} has timed out.')  
                if response.ok:
                    for chunk in response.iter_content(self.chunk_size):
                        if self.is_stop: # stop
                            return
                        while self.is_pause: # pause
                            sleep(0.01)
                        file.write(chunk)
                else:
                    if retry != 0:
                        logger.error(f'Request failure. status_code={response.status_code}. Try again.')
                        download_in_thread(file, retry - 1, start, end) # Implementing retry logic through recursion
                    else:
                        logger.error(f'Request failure. status_code={response.status_code}.')
                        raise RequestFailure(f'Request failure. status_code={response.status_code}')
                logger.info(f'A thread successfully downloaded the range ({start}-{end if end else ""}) of {self.url}.')
            except Exception as err_msg:
                err: str = repr(exc_info()[1])
                error_tuple = (
                    err.split('(')[0], # Get exception name
                    err_msg,
                    self.url
                )
                error_queue.put(error_tuple) # Store errors in the error queue
                logger.error(f'A thread encountered a {error_tuple[0]} while downloading {error_tuple[2]}: {error_tuple[1]}')

        # Create threads
        threads = []
        for i in range(self.num_threads):
            t = threading.Thread(target=download_in_thread, kwargs={
                'file': temps[i],
                'retry': retry,
                'start': ranges[i][0],
                'end': ranges[i][1],
            })
            threads.append(t)
            t.start()

        is_timeout = False
        # Waiting for all threads to complete
        for thread in threads:
            while True: # 1
                thread.join(self.thread_timeout if self.thread_timeout else None)
                if self.is_pause: # pause
                    while self.is_pause: # 2
                        sleep(0.01)
                    continue # Skip loop 1 and use join() method again。
                if self.is_stop: # stop
                    return self
                if thread.is_alive == True: # timeout
                    is_timeout = True
                    break
                break

        if is_timeout:
            if retry != 0:
                del temps # Release memory
                logger.error(f'A thread timed out while downloading {self.url} due to excessive execution time. Try again.')
                if retry:
                    return self.start(retry - 1)
                else:
                    return self.start(self.retry - 1)
            else:
                logger.error(f'A thread timed out while downloading {self.url} due to excessive execution time.')
                raise Timeout('Request timeout.')

        errors = []
        while not error_queue.empty():
            message = error_queue.get()
            errors.append(f'An {message[0]} occurred while downloading {message[2]}: {message[1]}')

        if len(errors) != 0:
            m = '[\n'
            for e in errors:
                m += f'\t"{e}",\n'
            m += ']'
            raise DownloadErrorS(m)
        else:
            # Merge all content
            logger.info('Merging all ranges.')
            f = open(temporary_file_name, 'wb')
            for i in temps:
                i.seek(0)
                f.write(i.read())
                i.close()
            f.close()
            rename(temporary_file_name, self.filename)

        logger.info(f'Successfully downloaded from {self.url} to {self.filename}.')
        return self

def download(
        url: str, filename: str,
        proxies: Union[HttpProxy, SocksProxy, NoProxy]=NoProxy(), timeout: float=None, retry: int=0, headers: dict={},
        chunk_size: int=1024 * 8
    ):
    '''
    A regular file download function.

    :param url: the URL of the file that needs to be downloaded
    :param file: file path (can be a relative path)
    :param proxies: HTTP/SOCKS proxy object, default value is an instance of NoProxy (indicating not using a proxy)
    :param timeout: how long to wait is considered timeout, default is None
    :param retry: the number of retries after a failed request, default is 0
    :param headers: request header, default value is {}
    :param chunk_size:  unit for streaming download, default 8KB

    Note: Excessive retry can lead to RecursiveError
    '''
    logger.info(f'Start downloading {url} to {filename}, remaining retry attempts: {retry}.')
    temporary_file_name = filename + '.download'
    try:
        response = requests.get(url, stream=True, proxies=proxies.proxies, timeout=timeout, headers=headers)
    except Timeout:
        response = FakeResponse()
        logger.warning(f'The request for {url} has timed out.')
    if response.ok:
        f = open(temporary_file_name, 'wb')
        for chunk in response.iter_content(chunk_size): # Streaming download
            f.write(chunk)
        f.close()
        rename(temporary_file_name, filename)
    else:
        if retry != 0:
            logger.error(f'Request failure. status_code={response.status_code}. Try again.')
            download(url, filename, proxies, timeout, retry - 1, chunk_size) # Implementing retry logic through recursion
        else:
            logger.error(f'Request failure. status_code={response.status_code}.')
            raise RequestFailure(f'Request failure. status_code={response.status_code}')

    logger.info(f'Successfully downloaded from {url} to {filename}.')

def multithreading_downloadS(
        urls: List[str], filenames: List[str],
        proxies: Union[HttpProxy, SocksProxy, NoProxy]=NoProxy(), timeout: float=None, retry: int=0, headers: dict={},
        chunk_size: int=1024 * 8
    ):
    '''
    A function that downloads multiple files simultaneously through thread based parallelism.

    :param urls: List of URLs for files that need to be downloaded
    :param filenames: List of file paths (which can be relative paths)
    :param proxies: HTTP/SOCKS proxy object, default value is an instance of NoProxy (indicating not using a proxy)
    :param timeout: how long to wait is considered timeout, default is None
    :param retry: the number of retries after a failed request, default is 0
    :param headers: request header, default value is {}
    :param chunk_size:  unit for streaming download, default 8KB

    Note: Excessive retry can lead to RecursiveError
    '''
    error_queue = Queue()

    def download_in_thread(url: str, filename: str, retry: int=0):
        try:
            logger.info(f'Start downloading {url} to {filename}, remaining retry attempts: {retry}.')
            temporary_file_name = filename + '.download'
            try:
                response = requests.get(url, stream=True, proxies=proxies.proxies, timeout=timeout, headers=headers, allow_redirects=True)
            except Timeout:
                response = FakeResponse()
                logger.warning(f'The request for {url} has timed out.')
            if response.ok:
                f = open(temporary_file_name, 'wb')
                for chunk in response.iter_content():
                    f.write(chunk)
                f.close()
                rename(temporary_file_name, filename)
            else:
                if retry != 0:
                    logger.error(f'Request failure. status_code={response.status_code}. Try again.')
                    download_in_thread(url, filename, retry - 1) # Implementing retry logic through recursion
                else:
                    logger.error(f'Request failure. status_code={response.status_code}.')
                    raise RequestFailure(f'Request failure. status_code={response.status_code}')

            logger.info(f'Successfully downloaded from {url} to {filename}.')
        except Exception as err_msg:
            err: str=repr(exc_info()[1])
            error_tuple = (
                err.split('(')[0], # Get exception name
                err_msg,
                url,
                filename,
            )
            error_queue.put(error_tuple) # Store errors in the error queue
            logger.error(f'A thread encountered a {error_tuple[0]} while downloading {error_tuple[2]} to {error_tuple[3]}: {error_tuple[1]}')

    # Create threads
    threads = []
    for i in range(len(urls)):
        t = threading.Thread(target=download_in_thread, kwargs={
            'url': urls[i],
            'filename': filenames[i],
            'retry': retry,
        })
        threads.append(t)
        t.start()

    # Waiting for all threads to complete
    for thread in threads:
        thread.join()

    errors = []
    while not error_queue.empty():
        message = error_queue.get()
        errors.append(f'An {message[0]} occurred while downloading {message[2]} to {message[3]}: {message[1]}')

    if len(errors) != 0:
        m = '[\n'
        for e in errors:
            m += f'\t"{e}",\n'
        m += ']'
        raise DownloadErrorS(m)

def multithreading_download(
        url: str, filename: str,
        proxies: Union[HttpProxy, SocksProxy, NoProxy]=NoProxy(), timeout: float=None, retry: int=0, headers: dict={},
        num_threads: int=60, in_memory=False, thread_timeout: float= None,
        chunk_size: int=1024 * 8
):
    '''
    A function that accelerates downloading by simultaneously downloading multiple parts of a single file through thread based parallelism.

    :param url: the URL of the file that needs to be downloaded
    :param file: file path (can be a relative path)
    :param proxies: HTTP/SOCKS proxy object, default value is an instance of NoProxy (indicating not using a proxy)
    :param timeout: how long to wait is considered timeout, default is None
    :param retry: the number of retries after a failed request, default is 0
    :param headers: request header, default value is {}
    :param num_threads: number of threads, default is 60
    :param chunk_size:  unit for streaming download, default 8KB
    :param thread_timeout: same as timeout, but used to wait for threads
    :param in_memory:  whether to use memory to store temporary data, default is False

    Note:
    Excessive retry can lead to RecursiveError;
    If the downloaded file is not a binary file or the file size is less than 1MB, the download() function will be called directly
    '''
    logger.info(f'Start downloading {url} to {filename}, remaining retry attempts: {retry}.')
    session = Session()
    temporary_file_name = filename + '.download'

    resp_headers = session.head(
        url, proxies=proxies.proxies, headers=headers, allow_redirects=True
    ).headers.get('Content-Length', 0)
    size = int(resp_headers.get('Content-Length', 0)) # Note: The response header of the text file does not have "Content-Length"
    accept_ranges = resp_headers.get('Accept-Ranges', None)
    logger.debug(f'The size of {url} is {size}.')
    if size < 1024 * 1024: # 1 MB
        logger.warning(f'The size of {url} is less than 1MB or it is a text file. Do not use multi-threaded downloads.')
        download(url, filename, proxies, timeout, retry)
        return
    elif accept_ranges == None:
        logger.warning(f'"{urlparse(url).netloc}" does not support Range.')
        download(url, filename, proxies, timeout, retry)
        return
    else:
        error_queue = Queue()
        # Using temporary files to avoid excessive memory consumption,
        # or using memory to increase read and write performance
        temps = [(BytesIO if in_memory else TemporaryFile)() for i in range(num_threads)]
        ranges = [(i * (size // num_threads), (i + 1) * (size // num_threads) - 1) for i in range(num_threads)]
        ranges[-1] = (ranges[-1][0], None)

    def download_in_thread(file: IO, retry: int=0, start: int=0, end: Optional[int]=None):
        logger.info(f'A thread starts downloading the range ({start}-{end if end else ""}) of {url}, with a remaining retry count of {retry}.')
        file.seek(0)
        try:
            try:
                # If the value of Range is "bytes=<start>-", it will be downloaded from<start>all the way to the end of the file
                updated_headers = {'Range': f'bytes={start}-{end if isinstance(end, int) else ""}'}
                updated_headers.update(headers)
                response = session.get(url, stream=True, proxies=proxies.proxies, timeout=timeout, headers = updated_headers, allow_redirects=True)
            except Timeout:
                response = FakeResponse()
                logger.warning(f'The request for {url} has timed out.')  
            if response.ok:
                for chunk in response.iter_content(chunk_size):
                    file.write(chunk)
            else:
                if retry != 0:
                    logger.error(f'Request failure. status_code={response.status_code}. Try again.')
                    download_in_thread(file, retry - 1, start, end) # Implementing retry logic through recursion
                else:
                    logger.error(f'Request failure. status_code={response.status_code}.')
                    raise RequestFailure(f'Request failure. status_code={response.status_code}')
            logger.info(f'A thread successfully downloaded the range ({start}-{end if end else ""}) of {url}.')
        except Exception as err_msg:
            err: str = repr(exc_info()[1])
            error_tuple = (
                err.split('(')[0], # Get exception name
                err_msg,
                url
            )
            error_queue.put(error_tuple) # Store errors in the error queue
            logger.error(f'A thread encountered a {error_tuple[0]} while downloading {error_tuple[2]}: {error_tuple[1]}')

    # Create threads
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=download_in_thread, kwargs={
            'file': temps[i],
            'retry': retry,
            'start': ranges[i][0],
            'end': ranges[i][1],
        })
        threads.append(t)
        t.start()

    is_timeout = False
    # Waiting for all threads to complete
    for thread in threads:
        thread.join(thread_timeout if thread_timeout else None)
        if thread.is_alive == True: # timeout
            is_timeout = True

    if is_timeout:
        if retry != 0:
            del temps # Release memory
            logger.error(f'A thread timed out while downloading {url} due to excessive execution time. Try again.')
            multithreading_download(url, filename, proxies, timeout, retry - 1, headers, num_threads, in_memory, thread_timeout, chunk_size)
            return
        else:
            logger.error(f'A thread timed out while downloading {url} due to excessive execution time.')
            raise Timeout('Request timeout.')

    errors = []
    while not error_queue.empty():
        message = error_queue.get()
        errors.append(f'An {message[0]} occurred while downloading {message[2]}: {message[1]}')

    if len(errors) != 0:
        m = '[\n'
        for e in errors:
            m += f'\t"{e}",\n'
        m += ']'
        raise DownloadErrorS(m)
    else:
        # Merge all content
        logger.info('Merging all ranges.')
        f = open(temporary_file_name, 'wb')
        for i in temps:
            i.seek(0)
            f.write(i.read())
            i.close()
        f.close()
        rename(temporary_file_name, filename)

    logger.info(f'Successfully downloaded from {url} to {filename}.')
