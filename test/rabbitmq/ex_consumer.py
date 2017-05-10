#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""To do
"""
import json
import logging
import os
import time
import queue
import concurrent.futures
import pika

LOG_FORMAT = ('%(levelname) -10s | %(asctime)s %(name) -20s | %(funcName) '
              '-30s | %(lineno) -5d | %(message)s')
LOGGER = logging.getLogger(__name__)

def do_real_work(request):
    """To do
    """
    print('[work start] time: %f, pid: %d, request: %r', 
          (time.time(), os.getpid(), request))
    time.sleep(3)
    result_data = {"status": "OK", "reply_to": 'render_response_rk', "xpath": "c:/footage/文件名.aepx"}
    print('[work end] time: %f, pid: %d, result_data: %r',
          (time.time(), os.getpid(), result_data))
    return result_data

class RenderWorker(object):
    """To do
    """
    def __init__(self, handler, render_request_q, render_result_q):
        self.handler = handler
        self.render_request_q = render_request_q
        self.render_result_q = render_result_q

def queue_get_nowait(q):
    """To do
    """
    if not isinstance(q, queue.Queue) or q.empty():
        return None
    try:
        item = q.get_nowait()
        q.task_done()
    except queue.Empty:
        return None
    return item

def queue_put_nowait(q, item):
    """To do
    """
    if not isinstance(q, queue.Queue) or q.full():
        return False
    try:
        q.put_nowait(item)
    except queue.Full:
        return False
    return True

def render_processing(render_worker):
    """To do
    """
    if not isinstance(render_worker, RenderWorker):
        return
    render_request_q = render_worker.render_request_q
    render_result_q = render_worker.render_result_q
    print('[render_process start] time: %f, pid: %d, ppid: %d',
          (time.time(), os.getpid(), os.getppid()))
    while True:
        render_request = queue_get_nowait(render_request_q)
        if render_request is not None:
            render_result = None
            try:
                render_result = render_worker.handler(render_request)
            except:
                print('[work_process exception]')
                continue
            if render_result is not None:
                queue_put_nowait(render_result_q, render_result)
            else:
                print('[render_process exception] render_result is None')
    print('[render_process end] time: %f, pid: %d, ppid: %d',
          (time.time(), os.getpid(), os.getppid()))

class ExConsumer(object):
    """To do
    """
    def __init__(self):
        self._config = {}
        self._closing = None
        self._connection = None
        self._channel = None
        self._render_request_q = None
        self._render_result_q = None
        self._render_pool_executor = None
        self._render_res_futures = set()

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
        LOGGER.info('[connect]')
        cred = pika.PlainCredentials(self._config['username'],
                                     self._config['password'])
        connect_params = pika.ConnectionParameters(self._config['host'],
                                                   self._config['port'],
                                                   virtual_host=self._config['virtual_host'],
                                                   credentials=cred)
        self._connection = pika.BlockingConnection(connect_params)
        self._channel = self._connection.channel()
        self._build_render_ex_and_q()

    def _reconnect(self):
        LOGGER.info('[reconnect]')
        if not self._closing:
            # Create a new connection
            self._connect()

    def _on_render_request(self, channel, method_frame, header_frame, body):
        render_request = json.loads(s=body.decode('utf-8'), encoding='utf-8')
        LOGGER.info('[consume] channel: %r, method_frame: %r, header_frame: %r, body: %r, render_request: %r',
                    channel, method_frame, header_frame, body, render_request)

    def _basic_consume_render_request(self):
        self._channel.basic_qos(prefetch_size=0, prefetch_count=1, all_channels=False)
        self._channel.basic_consume(consumer_callback=self._on_render_request,
                                    queue=self._config['render_request_q'],
                                    no_ack=True,
                                    exclusive=False,
                                    consumer_tag=None,
                                    arguments=None)
        LOGGER.info('[basic_consume]')

    def _basic_ack_render_request(self, tag):
        self._channel.basic_ack(delivery_tag=tag, multiple=False)
        LOGGER.info('[basic_ack]')

    def _basic_get_render_request(self):
        method_frame, header_frame, body = self._channel.basic_get(
            queue=self._config['render_request_q'], no_ack=True)
        if body is not None:
            render_request = json.loads(s=body.decode('utf-8'), encoding='utf-8')
            LOGGER.info('[basic_get] render_request: %r', render_request)
            return render_request
        return None

    def _validate_render_result(self, render_result):
        if isinstance(render_result, dict) and render_result.has_key('reply_to'):
            return True
        return False

    def _basic_publish_render_result(self, render_result):
        if not self._validate_render_result(render_result):
            return
        render_response = json.dumps(render_result, ensure_ascii=False)
        self._channel.basic_publish(exchange=self._config['render_ex'],
                                    routing_key=render_result['reply_to'],
                                    body=render_response.encode('utf-8'))
        LOGGER.info('[basic_publish] render_response: %r', render_response)

    def _submit_process_pool(self):
        self._render_request_q = queue.Queue(self._config['render_request_q_maxsize'])
        self._render_result_q = queue.Queue(self._config['render_result_q_maxsize'])
        self._render_pool_executor = concurrent.futures.ProcessPoolExecutor(
            self._config['render_max_workers'])
        for i in range(self._config['render_process_count']):
            render_worker = RenderWorker(handler=do_real_work,
                                         render_request_q=self._render_request_q,
                                         render_result_q=self._render_result_q)
            res_future = self._render_pool_executor.submit(render_processing, render_worker)
            self._render_res_futures.add(res_future)
            LOGGER.info('[submit process] i: %d, res_future: %r, render_res_futures: %r, render_worker: %r',
                        i, res_future, self._render_res_futures, render_worker)

    def _pull_render_request(self):
        if self._render_request_q.full():
            return
        render_request = self._basic_get_render_request()
        if render_request is not None:
            queue_put_nowait(self._render_request_q, render_request)

    def _process_render_result(self):
        while not self._render_result_q.empty():
            render_result = queue_get_nowait(self._render_result_q)
            if render_result is not None:
                LOGGER.info('[process result] render_result: %r', render_result)
                self._basic_publish_render_result(render_result)

    def load_config(self):
        """To do
        """
        self._config['host'] = 'localhost'
        self._config['port'] = 'port'
        self._config['virtual_host'] = '/'
        self._config['username'] = 'guest'
        self._config['password'] = 'guest'
        self._config['render_ex'] = 'render_ex'
        self._config['render_ex_type'] = 'direct'
        self._config['render_request_q'] = 'render_request_q'
        self._config['render_request_rk'] = 'render_request_rk'
        self._config['render_response_q'] = 'render_response_q'
        self._config['render_response_rk'] = 'render_response_rk'
        self._config['render_max_workers'] = 2
        self._config['render_request_q_maxsize'] = 2
        self._config['render_result_q_maxsize'] = 100
        self._config['rabbitmq_pull_interval'] = 10

    def setup_with_connect_params(self, host, port, virtual_host, username, password):
        """To do
        """
        LOGGER.info('[setup]')
        self._config['host'] = host
        self._config['port'] = port
        self._config['virtual_host'] = virtual_host
        self._config['username'] = username
        self._config['password'] = password

    def _disconnect(self):
        """To do
        """
        LOGGER.info('[disconnect]')
        self._closing = True
        if self._channel is not None and self._channel.is_open:
            self._channel.close()
            self._channel = None
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
            self._connection = None

    def stop(self):
        """To do
        """
        self._disconnect()
        if self._render_pool_executor is not None:
            self._render_pool_executor.shutdown()

    def run(self):
        """To do
        """
        self._connect()
        self._submit_process_pool()
        LOGGER.info('[main running] pid %r', os.getpid())
        while True:
            try:
                self._pull_render_request()
                self._process_render_result()
                self._connection.sleep(self._config['rabbitmq_pull_interval'])
                #self._connection.process_data_events(10)
            except pika.exceptions.ChannelClosed:
                LOGGER.exception('[exception]')
            except pika.exceptions.ConnectionClosed:
                LOGGER.exception('[exception]')
            except KeyboardInterrupt:
                LOGGER.exception('[exception]')
        self.stop()

def main():
    """To do
    """
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    ex = ExConsumer()
    ex.load_config()
    ex.setup_with_connect_params(host='localhost',
                                 port=5672,
                                 virtual_host='/',
                                 username='guest',
                                 password='guest')
    ex.run()

if __name__ == '__main__':
    main()
