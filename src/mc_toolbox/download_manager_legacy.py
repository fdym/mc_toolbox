# -*- coding: utf-8 -*-
#
#  download_manager_legacy.py
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
This module is an old implementation of the asynchronous download scheduler
and cannot specify SQLite database files for storage.
Please use mc_toolbox.download_manager instead.
'''
from collections import namedtuple
from typing import List, Tuple, Union, Iterable, Optional
import logging

from pony import orm

from .download import Downloader, MultithreadingDownloader, HttpProxy, SocksProxy, NoProxy, rename_if_exist
from .exception import DatabaseError
from .futures import MyProcessPoolExecutor, MyThreadPoolExecutor, DownloaderFuture
# class DatabaseError(Exception): pass

__all__ = [
    'Count',
    'DownloadTasks',
    'DownloadGroups',
    'get_task_count',
    'add_task_count',
    'get_group_count',
    'add_group_count',
    'initialization',
    'get_task_from_group',
    'get_group_from_task',
    'add_task',
    'get_task',
    'mod_task',
    'del_task',
    'exec_task',
    'exec_taskS',
]

logger = logging.getLogger(__name__)
db = orm.Database()
db.bind(provider='sqlite', filename='db.sqlite3', create_db=True)

class Count(db.Entity):
    number = orm.PrimaryKey(int, auto=False)
    count = orm.Required(int)

class DownloadTasks(db.Entity):
    task_id = orm.PrimaryKey(int, auto=False)
    name = orm.Required(str, unique=True, max_len=16)
    url = orm.Required(str, max_len=200)
    filename = orm.Required(str, max_len=128)
    is_thread = orm.Required(bool, default=False)
    downloading = orm.Required(bool, default=False)

class DownloadGroups(db.Entity):
    task_id = orm.PrimaryKey(int, auto=False)
    group_id = orm.Required(int)

db.generate_mapping(create_tables=True)

@orm.db_session
def get_task_count() -> int:
    '''
    Get the value of the task ID counter 
    (its value will be used to assign IDs when adding tasks).
    '''
    return Count.get(number=1).count

try:
    task_count = get_task_count()
except:
    task_count = None

@orm.db_session
def add_task_count():
    '''
    Increase the value of the task ID counter by one (its value will be used to assign IDs when adding tasks).
    '''
    global task_count
    if task_count == None:
        raise DatabaseError('"Count" data table is not initialization.')
    Count.get(number=1).set(count=task_count + 1)
    task_count += 1

@orm.db_session
def get_group_count() -> int:
    '''
    Get the value of the group task ID counter 
    (its value will be used to assign the group ID when adding the task).

    Tasks with the same group ID will be downloaded in parallel 
    when using mc_toolbox.download_manager_legacy.exec_taskS
    '''
    return Count.get(number=2).count

try:
    group_count = get_group_count()
except:
    group_count = None

@orm.db_session
def add_group_count():
    '''
    Increase the value of the group task ID counter by one 
    (its value will be used to assign the group ID when adding the task).

    Tasks with the same group ID will be downloaded in parallel 
    when using mc_toolbox.download_manager_legacy.exec_taskS
    '''
    global group_count
    if group_count == None:
        raise DatabaseError('"Count" data table is not initialization.')
    Count.get(number=2).set(count=group_count + 1)
    group_count += 1

def initialization():
    '''
    Initialization, which will result in all download tasks being deleted and two ID counters being reset.
    '''
    @orm.db_session
    def inner1():
        for i in ('DownloadTasks', 'DownloadGroups', 'Count'):
            db.execute(f'DROP TABLE IF EXISTS {i};')

    @orm.db_session
    def inner2():
        _task_count = Count(number=1, count=1)
        _group_count = Count(number=2, count=1)

    inner1()
    global task_count, group_count
    task_count, group_count = 1, 1
    db.create_tables()
    inner2()
    logger.info('The database has been initialized.')

@orm.db_session
def get_task_from_group(group_id: int) -> List[int]:
    '''
    Find all members of the group.

    :param group_id: Group ID
    '''
    result = []
    for task in DownloadGroups.select(lambda task: task.group_id == group_id):
        result.append(task.task_id)
    return result

@orm.db_session
def get_group_from_task(task_id: int) -> Optional[int]:
    '''
    Find the group to which the task belongs.

    :param task_id: Task ID

    Note: Returning None means that the task does not exist
    '''
    result = DownloadGroups.get(task_id=task_id)
    if result == None:
        logger.warning(f'The task with ID {task_id} does not exist.')
        return result
    return result.task_id

AddTaskNamedTuple = namedtuple('AddTaskNamedTuple', ('task_id', 'group_id'))

@orm.db_session
def add_task(name: str, url: str, filename: str, is_thread: bool=False) -> AddTaskNamedTuple[int, int]:
    '''
    Add task.

    :param name: task name (must be unique)
    :param url: URL
    :param filename: the path saved after downloading
    :param is_thread: representing the use of multi-threaded Boolean values

    Note: Returns a named tuple containing the task ID and group ID.
    '''
    task_id = get_task_count()
    add_task_count()
    group_id = get_group_count()
    logger.info(f'Add a download task named "{name}" from {url} to {filename}, {"" if is_thread else "without "}using multithreading. (ID is {task_id}, a member of group {group_id})')
    group = DownloadGroups(task_id=task_id, group_id=group_id)
    task = DownloadTasks(task_id=task_id, name=name, url=url, filename=filename, is_thread=is_thread, downloading=False)
    logger.info(f'Successfully added a download task named "{name}" from {url} to {filename}, {"" if is_thread else "without "}using multithreading. (ID is {task_id}, a member of group {group_id})')
    return AddTaskNamedTuple(task_id, group_id)

GetTaskNamedTuple = namedtuple('GetTaskNamedTuple', ('task_id', 'name', 'url', 'filename', 'is_thread', 'downloading'))

@orm.db_session
def get_task(name_or_id: Union[str, int]) -> GetTaskNamedTuple[int, str, str, str, bool, bool]:
    '''
    Get information about this task.

    :param name_or_id: the name or ID of this task

    Note: Returns a tuple containing task ID, task name, URL, filename, 
    boolean values indicating whether multi-threaded is being used and whether downloading is in progress.
    '''
    logger.info(f'Get a download task with the name or ID {name_or_id}.')
    if isinstance(name_or_id, str):
        task = DownloadTasks.get(name=name_or_id)
    else:
        task = DownloadTasks.get(task_id=name_or_id)
    return GetTaskNamedTuple(task.task_id, task.name, task.url, task.filename, task.is_thread, task.downloading)

@orm.db_session
def mod_task(
        name_or_id: Union[str, int],
        url: Optional[str]=None,
        filename: Optional[str]=None,
        is_thread: Optional[bool]=None,
        group_id: Optional[int]=None
    ) -> int:
    '''
    Modify task.

    :param name_or_id: task Name or Task ID
    :param url: URL
    :param filename: the path saved after downloading
    :param is_thread: representing the use of multi-threaded Boolean values
    :param group_id: group ID

    Except for the name_or_id attribute,
    all other attributes can be set to None and default to None (indicating no modification).
    '''
    logger.info(f'Start modifying a download task with the name or ID {name_or_id}.')
    if isinstance(name_or_id, str):
        task = DownloadTasks.get(name=name_or_id)
    else:

        task = DownloadTasks.get(task_id=name_or_id)
    if url:
        task.set(url=url)
        logger.info(f'The url for {name_or_id} has been changed to {url}.')
    if filename:
        task.set(filename=filename)
        logger.info(f'The filename for {name_or_id} has been changed to {filename}.')
    if is_thread:
        task.set(is_thread=is_thread)
        logger.info(f'Task {name_or_id} {"enabled" if is_thread else "disabled"} multi-threaded download.')
    if group_id:
        DownloadGroups.get(task_id=task.task_id).set(group_id=group_id)
        logger.info(f'The group_id for {name_or_id} has been changed to {group_id}.')
    logger.info(f'The modification of {name_or_id} has been completed.')
    return task.task_id

@orm.db_session
def del_task(name_or_id: Union[str, int]) ->GetTaskNamedTuple[int, str, str, str, bool, bool]:
    '''
    Delete task.

    :param name_or_id: task Name or Task ID

    Note: This function will provide the same return format as get_task.
    '''
    if isinstance(name_or_id, str):
        task = DownloadTasks.get(name=name_or_id)
        task_id = task.task_id
    else:
        task = DownloadTasks.get(task_id=name_or_id) 
        task_id = name_or_id
    group = DownloadGroups.get(task_id=task_id)
    result = GetTaskNamedTuple(task.task_id, task.name, task.url, task.filename, task.is_thread, task.downloading)   
    task.delete()
    group.delete()
    logger.info(f'{name_or_id} has been deleted.')
    return result

executor = MyProcessPoolExecutor()
thread_executor = MyThreadPoolExecutor()

@orm.db_session
def _set_downloading_to_false(name_or_id: Union[str, int], future=None):
    if isinstance(name_or_id, str):
        DownloadTasks.get(name=name_or_id).set(downloading=False)
    else:
        DownloadTasks.get(task_id=name_or_id).set(downloading=False)

ExecTaskNamedTuple = namedtuple('ExecTaskNamedTuple', ('downloader', 'future'))

@orm.db_session
def exec_task(
        name_or_id: Union[str, int],
        proxies: Union[HttpProxy, SocksProxy, NoProxy]=NoProxy(),
        timeout: float=None,
        retry: int=0,
        headers: dict={},
        num_threads: int=60,
        in_memory: bool=False,
        thread_timeout: float=None,
        chunk_size: int=1024 * 8,
        when_exist=rename_if_exist,
) -> ExecTaskNamedTuple[Union[Downloader, MultithreadingDownloader], DownloaderFuture]:
    '''
    Now, it's time to start a download task using this function.

    :param name_or_id: task name or task ID
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

    Note: If the task is set to not use multithreading, then num_thread, in_memory and thread_timeout properties will be ignored.
    '''
    task = get_task(name_or_id)
    if task.is_thread:
        kwargs = {
            'url': task.url,
            'filename': task.filename,
            'proxies': proxies,
            'timeout': timeout,
            'retry': retry,
            'headers': headers,
            'num_threads': num_threads,
            'in_memory': in_memory,
            'thread_timeout': thread_timeout,
            'chunk_size': chunk_size,
            'when_exist': when_exist
        }
        logger.info(f'Executing task {name_or_id}')
        logger.debug(f'All parameters passed to MultithreadingDownloader: {kwargs}')
        downloader = MultithreadingDownloader(**kwargs)
        if isinstance(name_or_id, str):
            DownloadTasks.get(name=name_or_id).set(downloading=True)
        else:
            DownloadTasks.get(task_id=name_or_id).set(downloading=True)
        future = executor.submit(downloader.start)
        future.add_done_callback(_set_downloading_to_false, name_or_id)
        return ExecTaskNamedTuple(downloader, future)
    else:
        kwargs = {
            'url': task.url,
            'filename': task.filename,
            'proxies': proxies,
            'timeout': timeout,
            'retry': retry,
            'headers': headers,
            'chunk_size': chunk_size,
            'when_exist': when_exist
        }
        logger.info(f'Executing task {name_or_id}')
        logger.debug(f'All parameters passed to Downloader: {kwargs}')
        downloader = Downloader(**kwargs)
        if isinstance(name_or_id, str):
            DownloadTasks.get(name=name_or_id).set(downloading=True)
        else:
            DownloadTasks.get(task_id=name_or_id).set(downloading=True)
        future = executor.submit(downloader.start)
        future.add_done_callback(_set_downloading_to_false, name_or_id)
        return ExecTaskNamedTuple(downloader, future)

def exec_taskS(
        group_id: int,
        proxies: Union[HttpProxy, SocksProxy, NoProxy]=NoProxy(),
        timeout: float=None,
        retry: int=0,
        headers: dict={},
        num_thread: int=60,
        in_memory: bool=False,
        thread_timeout: float=None,
        chunk_size: int=1024 * 8,
        when_exist=rename_if_exist,
) -> Iterable[ExecTaskNamedTuple[Union[Downloader, MultithreadingDownloader], DownloaderFuture]]:
    '''
    Use this GENERATOR to execute all tasks within a group.

    :param group_id: group ID
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

    Note: If the task is set to not use multithreading, then num_thread, in_memory and thread_timeout properties will be ignored.
    '''
    logger.info(f'Execute all tasks with group ID {group_id}.')
    task_id_list = get_task_from_group(group_id)
    for task_id in task_id_list:
        task = get_task(task_id)
        if task.is_thread:
            kwargs = {
                'url': task.url,
                'filename': task.filename,
                'proxies': proxies,
                'timeout': timeout,
                'retry': retry,
                'headers': headers,
                'num_thread': num_thread,
                'in_memory': in_memory,
                'thread_timeout': thread_timeout,
                'chunk_size': chunk_size,
                'when_exist': when_exist
            }
            logger.info(f'Executing task {task_id}')
            logger.debug(f'All parameters passed to MultithreadingDownloader: {kwargs}')
            downloader = MultithreadingDownloader(**kwargs)
            DownloadTasks.get(task_id=task_id).set(downloading=True)
            future = executor.submit(downloader.start)
            future.add_done_callback(_set_downloading_to_false, task_id)
            yield ExecTaskNamedTuple(downloader, future)
        else:
            kwargs = {
                'url': task.url,
                'filename': task.filename,
                'proxies': proxies,
                'timeout': timeout,
                'retry': retry,
                'headers': headers,
                'chunk_size': chunk_size,
                'when_exist': when_exist
            }
            logger.info(f'Executing task {task_id}')
            logger.debug(f'All parameters passed to Downloader: {kwargs}')
            downloader = Downloader(**kwargs)
            DownloadTasks.get(task_id=task_id).set(downloading=True)
            future = thread_executor.submit(downloader.start) # thread_executor
            future.add_done_callback(_set_downloading_to_false, task_id)
            yield ExecTaskNamedTuple(downloader, future)
