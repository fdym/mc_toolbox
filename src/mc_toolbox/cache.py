# -*- coding: utf-8 -*-
#
#  cache.py
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
Provide thread safe caching.
'''
from collections import OrderedDict
from functools import wraps
from time import monotonic, sleep
from typing import Any, Optional, Tuple, Set, Callable
import logging
import threading

__all__ = [
    'CacheManager',
]

logger = logging.getLogger(__name__)

class CacheManager:
    '''
    A thread safe cache manager.

    :param max_size: Maximum cache capacity, default 100
    :param ttl: Cache entry lifetime, default is one hour
    '''
    def __init__(self, max_size: int=100, ttl: int=3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache = OrderedDict()
        self._lock = threading.Lock()
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        '''
        Start the cleaning thread.
        '''
        def cleanup():
            while True:
                self._remove_expired()
                sleep(self.ttl / 2)  # Perform cleaning once every half lifetime.
                
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()

    def set_cache(self, key: Any, value: Any):
        '''
        Add or update cache entries.
        You should already know how to use these two parameters.
        '''
        with self._lock:
            # Check capacity
            if len(self._cache) >= self.max_size:
                k = self._cache.popitem(last=False)[0]
                logger.debug(f'Remove "{k}".')
            # Store entries and timestamps
            self._cache[key] = (monotonic(), value)
            self._cache.move_to_end(key)
            logger.debug(f'Set "{key}"')

    def get_cache(self, key: Any) -> Optional[Any]:
        '''
        Retrieve cache entries.
        You should already know how to use this parameter.
        Return the value pointed to by the parameter key.
        '''
        with self._lock:
            timestamp, value = self._cache.get(key, (0, None))
            if monotonic() - timestamp < self.ttl:
                return value
            self._cache.pop(key, None)  # Remove expired entries
            return None

    def delete(self, key) -> Optional[Any]:
        '''
        Delete cache entries.
        You should already know how to use this parameter.
        Return the value pointed to by the parameter key.
        '''
        with self._lock:
            logger.debug(f'Remove "{key}".')
            return self._cache.pop(key, None)

    def clear(self):
        '''
        Clear all cache.
        '''
        with self._lock:
            self._cache.clear()
            logger.debug('Clear all cache.')

    @property
    def keys(self) -> Set[Any]:
        with self._lock:
            return set(self._cache.keys())

    @property
    def values(self) -> Tuple[Any]:
        with self._lock:
            return tuple(self._cache.values())

    @property
    def items(self) -> Tuple[Tuple[Any, Any]]:
        with self._lock:
            return tuple(self._cache.items())

    def _remove_expired(self):
        '''
        Remove expired entries.
        '''
        with self._lock:
            current_time = monotonic()
            expired_keys = [
                k for k, (ts, _) in self._cache.items()
                if current_time - ts >= self.ttl
            ]
            for k in expired_keys:
                del self._cache[k]
                logger.debug(f'Remove "{k}".')

    def cache(self, key: Any) -> Callable:
        '''
        A simple constructor for cache decorators.

        :param key: The name of the key used.

        Return a function that is a true decorator.
        '''
        def wrapper(func):
            @wraps(func)
            def inner(*args, **kwargs):
                if self.get_cache(key):
                    cache = self.get_cache(key)
                else:
                    cache = func(*args, **kwargs)
                    self.set_cache(key, cache)
                return cache
            return inner
        return wrapper
