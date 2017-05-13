#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""To do
   it is for python3
"""
import os
import sys
import getopt
import io
import json
import time
import logging
from optparse import OptionParser
import multiprocessing
import queue  #for python3
import concurrent.futures
import pika

LOG_FORMAT = ('%(levelname) -10s | %(asctime)s %(name) -20s | %(funcName) '
              '-30s | %(lineno) -5d | %(message)s')
LOGGER = logging.getLogger(__name__)

def do_real_work(request):
    """To do
    """
    print('[mywork start] time: %f, pid: %d, ppid: %d, request: %r, request_size: %d' %
          (time.time(), os.getpid(), os.getppid(), request, sys.getsizeof(request)))
    time.sleep(10)
    if not isinstance(request, dict):
        print('[mywork error] request is not dict, request: %r', request)
        return None
    result = request
    result["status"] = "OK"
    result["xpath"] = "c:/footage/视频.mov"
    print('[mywork end] time: %f, pid: %d, ppid: %d, result: %r, result_size: %d' %
          (time.time(), os.getpid(), os.getppid(), result, sys.getsizeof(result)))
    return result

class RenderWorker(object):
    """To do
    """
    def __init__(self, handler, request=None, lock=None,
                 render_request_q=None, render_result_q=None,
                 pending_request_count=None):
        self.handler = handler
        self.request = request
        self.lock = lock
        self.render_request_q = render_request_q
        self.render_result_q = render_result_q
        self.pending_request_count = pending_request_count

    def run(self, *args, **kwargs):
        """To do
        """
        print('[render work run] args: %r, kwargs: %r' % (args, kwargs))
        if not callable(self.handler):
            print('[render work fail] handle is not callable: %r')
        result = None
        result = self.handler(*args, **kwargs)
        return result

def json_loads(json_bytes):
    """To do
    """
    json_data = None
    try:
        json_data = json.loads(s=json_bytes.decode('utf-8'), encoding='utf-8')
    except ValueError as expt:
        json_data = None
        print('[json loads error] e: %r' % expt)
    return json_data

def json_dumps(json_data):
    """To do
    """
    json_bytes = None
    try:
        json_bytes = (json.dumps(obj=json_data, ensure_ascii=False)).encode('utf-8')
    except TypeError as expt:
        json_bytes = None
        print('[json dumps error] e: %r' % expt)
    except ValueError:
        json_bytes = None
        print('[json dumps error] e: %r' % expt)
    except OverflowError:
        json_bytes = None
        print('[json dumps error] e: %r' % expt)
    return json_bytes

def queue_get_nowait(myqueue):
    """To do
    """
    if myqueue.empty():
        return None
    item = None
    try:
        item = myqueue.get_nowait()
        myqueue.task_done()
    except queue.Empty:
        return None
    return item

def queue_put_nowait(myqueue, item):
    """To do
    """
    if myqueue.full():
        return False
    try:
        myqueue.put_nowait(item)
    except queue.Full:
        return False
    return True

def render_processing_forever(render_worker):
    """To do
    """
    if not isinstance(render_worker, RenderWorker):
        print('[render_process_forever warn] render_worker is invalid: %r' % render_worker)
        return
    lock = render_worker.lock
    render_request_q = render_worker.render_request_q
    render_result_q = render_worker.render_result_q
    pending_request_count = render_worker.pending_request_count
    print('[render_process_forever start] time: %f, pid: %d, ppid: %d, '
          'render_request_qsize: %d, render_result_qsize: %d' %
          (time.time(), os.getpid(), os.getppid(),
           render_request_q.qsize(), render_result_q.qsize()))
    # main loop
    while True:
        render_request = queue_get_nowait(render_request_q)
        if render_request is None:
            print('[render_process_forever warn] render_request is None')
        with lock:
            pending_request_count.value -= 1
        print('[render_process_forever handler request] time: %f, pid: %d, ppid: %d, '
              'render_request_qsize: %d, render_result_qsize: %d'
              'request: %r, request_size: %d' %
              (time.time(), os.getpid(), os.getppid(),
               render_request_q.qsize(), render_result_q.qsize(),
               render_request, sys.getsizeof(render_request)))
        render_result = None
        try:
            # user handler
            render_result = render_worker.handler(render_request)
            if render_result is not None:
                print('[render_process_forever handler result] time: %f, pid: %d, ppid: %d, '
                      'render_request_qsize: %d, render_result_qsize: %d'
                      'result: %r, result_size: %d' %
                      (time.time(), os.getpid(), os.getppid(),
                       render_request_q.qsize(), render_result_q.qsize(),
                       render_result, sys.getsizeof(render_result)))
                queue_put_nowait(render_result_q, render_result)
            else:
                print('[render_process_forever warn] render_result is None')
        except:
            print('[render_process_forever exception] work handler exception')
            continue
    print('[render_process_forever end] time: %f, pid: %d, ppid: %d, '
          'render_request_qsize: %d, render_result_qsize: %d' %
          (time.time(), os.getpid(), os.getppid(),
           render_request_q.qsize(), render_result_q.qsize()))

def render_processing_onetime(render_worker):
    """To do
    """
    if not isinstance(render_worker, RenderWorker):
        print('[render_processing_onetime warn] render_worker is invalid: %r' % render_worker)
        return None
    print('[render_process_onetime start] time: %f, pid: %d, ppid: %d' %
          (time.time(), os.getpid(), os.getppid()))
    render_request = render_worker.request
    if render_request is None:
        print('[render_processing_onetime warn] render_request is None')
    print('[render_process_onetime handler request] time: %f, pid: %d, ppid: %d, '
          'request: %r, request_size: %d' %
          (time.time(), os.getpid(), os.getppid(),
           render_request, sys.getsizeof(render_request)))
    render_result = None
    try:
        # user handler
        render_result = render_worker.run(request=render_request)
        if render_result is not None:
            print('[render_process_onetime handler result] time: %f, pid: %d, ppid: %d, '
                  'result: %r, result_size: %d' %
                  (time.time(), os.getpid(), os.getppid(),
                   render_result, sys.getsizeof(render_result)))
        else:
            print('[render_process_onetime warn] render_result is None')
    except:
        render_result = None
        print('[render_process_onetime exception] work handler exception')
    print('[render_process_onetime end] time: %f, pid: %d, ppid: %d, '
          'result: %r, result_size: %d' %
          (time.time(), os.getpid(), os.getppid(),
           render_result, sys.getsizeof(render_result)))
    return render_result

class ExConsumer(object):
    """To do
    """
    def __init__(self):
        self._config = {}
        self._closing = None
        self._connection = None
        self._channel = None
        self._monitor_timestamp = None
        self._pending_request_count = None
        self._render_pool_executor = None
        self._render_res_futures = None
        self._render_process_manager = None
        self._render_process_lock = None
        self._render_request_q = None
        self._render_result_q = None

    def _build_render_ex_and_q(self):
        self._channel.exchange_declare(exchange=self._config['render_ex'],
                                       exchange_type=self._config['render_ex_type'],
                                       passive=False,
                                       durable=False,
                                       auto_delete=False,
                                       internal=False,
                                       arguments=None)
        self._channel.queue_declare(queue=self._config['render_request_q'],
                                    passive=False,
                                    durable=False,
                                    exclusive=False,
                                    auto_delete=False,
                                    arguments=None)
        self._channel.queue_bind(queue=self._config['render_request_q'],
                                 exchange=self._config['render_ex'],
                                 routing_key=self._config['render_request_rk'])

    def _connect(self):
        cred = pika.PlainCredentials(self._config['username'],
                                     self._config['password'])
        connect_params = pika.ConnectionParameters(self._config['host'],
                                                   self._config['port'],
                                                   virtual_host=self._config['virtual_host'],
                                                   credentials=cred)
        self._connection = pika.BlockingConnection(connect_params)
        if not self._connection.is_open:
            LOGGER.error('[connect fail] cannot open rabbitmq connection, '
                         'cred: %r, connect_params: %r',
                         cred, connect_params)
            return False
        self._channel = self._connection.channel()
        if not self._channel.is_open:
            LOGGER.error('[connect fail] cannot open rabbitmq channel, '
                         'cred: %r, connect_params: %r',
                         cred, connect_params)
            return False
        self._build_render_ex_and_q()
        LOGGER.info('[connect success] connect to rabbitmq, connection :%r, channel: %r, '
                    'cred: %r, connect_params: %r',
                    self._connection, self._channel,
                    cred, connect_params)
        return True

    def _disconnect(self):
        """To do
        """
        if self._channel is not None and self._channel.is_open:
            self._channel.close()
            self._channel = None
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
            self._connection = None
        LOGGER.info('[disconnect]')

    def _reconnect(self):
        LOGGER.info('[reconnect]')
        # Create a new connection
        try_attemp = 3
        i = 0
        while i < try_attemp:
            self._disconnect()
            time.sleep(10)
            if not self._connect():
                i += 1
            else:
                break
        if i == try_attemp:
            LOGGER.error('[reconnect fail]')
            return False
        LOGGER.info('[reconnect success]')
        return True

    def _on_render_request(self, channel, method_frame, header_frame, body):
        render_request = json_loads(body)
        LOGGER.info('[consume] channel: %r, method_frame: %r, '
                    'header_frame: %r, body: %r, render_request: %r',
                    channel, method_frame, header_frame, body, render_request)

    def _basic_consume_render_request(self):
        self._channel.basic_qos(prefetch_size=0, prefetch_count=1, all_channels=False)
        self._channel.basic_consume(consumer_callback=self._on_render_request,
                                    queue=self._config['render_request_q'],
                                    no_ack=False,
                                    exclusive=False,
                                    consumer_tag=None,
                                    arguments=None)
        LOGGER.info('[basic_consume]')

    def _basic_ack_render_request(self, delivery_tag):
        self._channel.basic_ack(delivery_tag=delivery_tag, multiple=False)
        LOGGER.info('[basic_ack] delivery_tag: %r', delivery_tag)

    def _basic_get_render_request(self):
        method_frame, header_frame, body = self._channel.basic_get(
            queue=self._config['render_request_q'],
            no_ack=True)
        if body is None:
            return None
        render_request = json_loads(body)
        if render_request is None:
            LOGGER.error('[basic_get fail] render_request is None, '
                         'body: %r', body)
            return None
        LOGGER.info('[basic_get] body: %r, render_request_size: %d',
                    body, sys.getsizeof(render_request))
        return render_request

    def _validate_render_result(self, render_result):
        # json is a dict type in python
        if render_result is None:
            return False
        if isinstance(render_result, dict) and ('reply_to' in render_result):
            return True
        return False

    def _basic_publish_render_result(self, render_result):
        if not self._validate_render_result(render_result):
            LOGGER.error('[validate_render_result fail] render_result: %r', render_result)
            return
        render_response = json_dumps(render_result)
        if render_response is None:
            LOGGER.error('[json dumps error] render_response is None, '
                         'render_result: %r', render_result)
            return
        self._channel.basic_publish(exchange=self._config['render_ex'],
                                    routing_key=render_result['reply_to'],
                                    body=render_response)
        LOGGER.info('[basic_publish] render_response: %r', render_response)

    def _create_process_pool_with_queue(self):
        self._render_process_manager = multiprocessing.Manager()
        self._render_process_lock = multiprocessing.Lock()
        self._pending_request_count = self._render_process_manager.Value('i', 0, lock=True)
        self._render_request_q = self._render_process_manager.Queue()
        self._render_result_q = self._render_process_manager.Queue()
        self._render_pool_executor = concurrent.futures.ProcessPoolExecutor(
            self._config['render_max_workers'])
        self._render_res_futures = set()
        i = 0
        while i < self._config['render_max_workers']:
            render_worker = RenderWorker(handler=do_real_work,
                                         lock=self._render_process_lock,
                                         render_request_q=self._render_request_q,
                                         render_result_q=self._render_result_q,
                                         pending_request_count=self._pending_request_count)
            res_future = self._render_pool_executor.submit(render_processing_forever, render_worker)
            self._render_res_futures.add(res_future)
            LOGGER.info('[submit process_forever] i: %d, res_future: %r, render_res_futures: %r,'
                        'render_worker: %r, render_request_q_size: %d, render_result_q_size: %d',
                        i, res_future, self._render_res_futures, render_worker,
                        self._render_request_q.qsize(), self._render_result_q.qsize())

    def _pull_render_request_into_queue(self):
        if self._render_request_q.full():
            return
        with self._render_process_lock:
            if self._pending_request_count.value < self._config['pending_request_count']:
                self._pending_request_count.value += 1
            else:
                print('[pending request] pending_request_count: %d' %
                      self._pending_request_count.value)
                return
        render_request = self._basic_get_render_request()
        if render_request is not None:
            queue_put_nowait(self._render_request_q, render_request)

    def _process_render_result_from_queue(self):
        while not self._render_result_q.empty():
            render_result = queue_get_nowait(self._render_result_q)
            if render_result is not None:
                LOGGER.info('[process result] render_result: %r, render_result_size: %d',
                            render_result, sys.getsizeof(render_result))
                self._basic_publish_render_result(render_result)

    def _create_process_pool(self):
        self._render_pool_executor = concurrent.futures.ProcessPoolExecutor(
            self._config['render_max_workers'])
        self._render_res_futures = set()

    def _submit_render_work(self, render_request):
        if render_request is None:
            return
        render_worker = RenderWorker(handler=do_real_work, request=render_request)
        res_future = self._render_pool_executor.submit(render_processing_onetime, render_worker)
        self._render_res_futures.add(res_future)
        LOGGER.info('[submit process_onetime] res_future: %r, render_res_futures: %r,'
                    'render_worker: %r',
                    res_future, self._render_res_futures, render_worker)

    def _pull_render_request(self):
        if len(self._render_res_futures) >= self._config['pending_request_count']:
            return
        render_request = self._basic_get_render_request()
        if render_request is not None:
            self._submit_render_work(render_request)

    def _process_render_result(self):
        res_remove_set = set()
        for res_future in self._render_res_futures:
            if res_future.done():
                res_remove_set.add(res_future)
        for res_future in res_remove_set:
            self._render_res_futures.remove(res_future)
            render_result = res_future.result()
            LOGGER.info('[processing result] render_result: %r, render_result_size: %d',
                        render_result, sys.getsizeof(render_result))
            if render_result is not None:
                self._basic_publish_render_result(render_result)
        res_remove_set_len = len(res_remove_set)
        if res_remove_set_len > 0:
            LOGGER.info('[process after result] self._render_res_futures: %r, res_remove_set: %r',
                        self._render_res_futures, res_remove_set)
        res_remove_set.clear()

    def _monitor(self):
        now_time = time.time()
        if now_time > self._monitor_timestamp:
            if self._render_res_futures is not None:
                LOGGER.info('[monitor] render_res_futures: %r', self._render_res_futures)
            self._monitor_timestamp = now_time + self._config['monitor_interval']

    def _default_config(self):
        self._config['host'] = 'localhost'
        self._config['port'] = 5672
        self._config['virtual_host'] = '/'
        self._config['username'] = 'guest'
        self._config['password'] = 'guest'
        self._config['render_ex'] = 'render_ex'
        self._config['render_ex_type'] = 'direct'
        self._config['render_request_q'] = 'render_request_q'
        self._config['render_request_rk'] = 'render_request_rk'
        self._config['render_response_q'] = 'render_response_q'
        self._config['render_response_rk'] = 'render_response_rk'
        self._config['render_max_workers'] = 3
        self._config['pending_request_count'] = 2
        self._config['rabbitmq_pull_interval'] = 30
        self._config['monitor_interval'] = 60
        self._config['render_request_q_maxsize'] = 1024 * 1024
        self._config['render_result_q_maxsize'] = 1024 * 1024

    def configure(self, options=None):
        """To do
        """
        self._default_config()
        if options.host:
            self._config['host'] = options.host
        if options.port:
            self._config['port'] = options.port
        if options.username:
            self._config['username'] = options.username
        if options.password:
            self._config['password'] = options.password
        if options.render_max_workers:
            self._config['render_max_workers'] = options.render_max_workers
        if options.pending_request_count:
            self._config['pending_request_count'] = options.pending_request_count
        LOGGER.info('[config] %r', self._config)

    def _stop(self):
        LOGGER.info('[stoping...] pid: %d, render_res_futures: %r',
                    os.getpid(), self._render_res_futures)
        self._disconnect()
        if self._render_res_futures is not None:
            for res_future in self._render_res_futures:
                res_future.cancel()
            self._render_res_futures.clear()
        if self._render_pool_executor is not None:
            self._render_pool_executor.shutdown()
        if self._render_process_manager is not None:
            self._render_process_manager.shutdown()
        LOGGER.info('[stop success] pid: %d, render_res_futures: %r',
                    os.getpid(), self._render_res_futures)

    def _run(self):
        if not self._connect():
            LOGGER.error('[connect fail] cannot connect to rabbitmq')
            return
        self._create_process_pool()
        self._monitor_timestamp = time.time()
        self._closing = True
        LOGGER.info('[main process running] pid: %d', os.getpid())
        while self._closing:
            try:
                self._pull_render_request()
                self._process_render_result()
                self._monitor()
                self._connection.sleep(self._config['rabbitmq_pull_interval'])
                #self._connection.process_data_events(10)
            except pika.exceptions.ChannelClosed as expt:
                LOGGER.exception('[exception] e: %r', expt)
            except pika.exceptions.ConnectionClosed:
                LOGGER.exception('[exception] e: %r', expt)
            except KeyboardInterrupt:
                self._closing = False
                LOGGER.exception('[exception]')

    def start(self):
        """To do
        """
        self._run()
        self._stop()

def logging_config():
    """To do
    """
    logging.basicConfig(level=logging.INFO,
                        format=LOG_FORMAT,
                        #filename='logs/ae_consumer.log',
                        #filemode='a+'
                       )
    #console = logging.StreamHandler()
    #console.setLevel(logging.INFO)
    #logging.getLogger('').addHandler(console)

def server_run(options):
    """To do
    """
    LOGGER.info('*************************************************')
    LOGGER.info('*                ae rabbitmq consumer           *')
    LOGGER.info('*************************************************')
    LOGGER.info('*** Render server run, pid: %d ***', os.getpid())
    ex = ExConsumer()
    ex.configure(options)
    ex.start()
    LOGGER.info('*** Render server terminated, pid: %d ***', os.getpid())

def main():
    """To do
    """
    logging_config()
    usage = "usage: %prog [options] arg1[, arg2...]"
    parser = OptionParser(usage=usage, version="%prog 1.0")
    parser.add_option("--host",
                      action="store", dest="host", type="string",
                      default='localhost', help="set rabbitmq host")
    parser.add_option("--port",
                      action="store", dest="port", type="int",
                      default=5672, help="set rabbitmq port")
    parser.add_option("-u", "--username",
                      action="store", dest="username", type="string",
                      default='guest', help="set rabbitmq username")
    parser.add_option("-p", "--password",
                      action="store", dest="password", type="string",
                      default='guest', help="set rabbitmq password")
    parser.add_option("--pending_request_count",
                      action="store", dest="pending_request_count", type="int",
                      help="set pending_request_count")
    parser.add_option("-w", "--render_max_workers",
                      action="store", dest="render_max_workers", type="int",
                      help="set render_max_workers")
    (options, args) = parser.parse_args()
    LOGGER.info('[cmd options] options: %r, args: %r', options, args)
    # main loop
    server_run(options)

if __name__ == '__main__':
    main()
