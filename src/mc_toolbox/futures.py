'''
This module has made some customization to the asynchronous executor in concurrent.futures
'''
from concurrent.futures import ProcessPoolExecutor, Future
from concurrent.futures._base import CANCELLED, CANCELLED_AND_NOTIFIED, FINISHED
from concurrent.futures.process import _WorkItem, BrokenProcessPool, _global_shutdown
import logging

__all__ = [
    'DownloaderFuture',
    'MyProcessPoolExecutor',
]

logger = logging.getLogger(__name__)

class DownloaderFuture(Future):
    def _invoke_callbacks(self):
        for callback in self._done_callbacks:
            try:
                kwargs = callback[2]
                kwargs.update({'future': self})
                callback[0](*callback[1], **kwargs)
            except Exception:
                logger.exception('exception calling callback for %r', self)

    def add_done_callback(self, fn, *args, **kwargs):
        '''
        This modified method can attach functions to the DownloaderFuture object
        and call the attached functions when the DownloaderFuture object is completed or canceled.

        fn: callable function
        args and kwargs are parameters passed to fn

        Note: When the DownloaderFuture instance executes fn,
              it will be passed as an additional keyword parameter 'future' to fn.        
        '''
        with self._condition:
            if self._state not in [CANCELLED, CANCELLED_AND_NOTIFIED, FINISHED]:
                self._done_callbacks.append((fn, args, kwargs))
                return
        try:
            kwargs.update({'future': self})
            fn(*args, **kwargs)
        except Exception:
            logger.exception('exception calling callback for %r', self)

class MyProcessPoolExecutor(ProcessPoolExecutor):
    def submit(self, fn, /, *args, **kwargs):
        with self._shutdown_lock:
            if self._broken:
                raise BrokenProcessPool(self._broken)
            if self._shutdown_thread:
                raise RuntimeError('cannot schedule new futures after shutdown')
            if _global_shutdown:
                raise RuntimeError('cannot schedule new futures after '
                                   'interpreter shutdown')

            f = DownloaderFuture()
            w = _WorkItem(f, fn, args, kwargs)

            self._pending_work_items[self._queue_count] = w
            self._work_ids.put(self._queue_count)
            self._queue_count += 1
            # Wake up queue management thread
            self._executor_manager_thread_wakeup.wakeup()

            if self._safe_to_dynamically_spawn_children:
                self._adjust_process_count()
            self._start_executor_manager_thread()
            return f
    submit.__doc__ = ProcessPoolExecutor.submit.__doc__

# def test(content, future):
#     print(content)

# MyProcessPoolExecutor().submit(print, 'hello').add_done_callback(test, 'world')
