#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""To do
"""
import json
import logging
import os
import time
import Queue
import concurrent.futures
import pika

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -20s %(funcName) '
              '-30s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

def do_real_work(request):
    """To do
    """
    LOGGER.info('[doing work...]')
    time.sleep(3)
    json_data = {"status": "OK", "xpath": "c:/output/视频.mov"}
    print('[work result] %r', json_data)
    return json_data

class RenderWork(object):
    """To do
    """
    def __init__(self, handler, render_request_q, render_result_q):
        self.handler = handler
        self.render_request_q = render_request_q
        self.render_result_q = render_result_q
        self.test = 1

def queue_get_nowait(queue):
    """To do
    """
    if not isinstance(queue, Queue) or queue.empty():
        return None
    try:
        item = queue.get_nowait()
        queue.task_done()
    except Queue.Empty:
        return None
    return item

def queue_put_nowait(queue, item):
    """To do
    """
    if not isinstance(queue, Queue) or queue.full():
        return False
    try:
        queue.put_nowait(item)
    except Queue.Full:
        return False
    return True

def render_processing(render_work):
    """To do
    """
    print('[render_processing start] %r | %r', os.getpid(), os.getppid())
    if not isinstance(render_work, RenderWork):
        return
    render_request_q = render_work.render_request_q
    render_result_q = render_work.render_result_q
    while True:
        render_request = queue_get_nowait(render_request_q)
        if render_request is not None:
            render_result = render_work.do_work(render_request)
            if render_result is not None:
                queue_put_nowait(render_result_q, render_result)
    print('[render_processing stop] %r | %r', os.getpid(), os.getppid())

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
        self._render_request = None
        self._render_response = None
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
        LOGGER.info('[consume] %r | %r | %r | %r | %r',
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
            LOGGER.info('[basic_get] %r', render_request)
            return render_request
        return None

    def _basic_publish_render_result(self, render_result):
        render_response = json.dumps(render_result, ensure_ascii=False)
        self._channel.basic_publish(exchange=self._config['render_ex'],
                                    routing_key=render_result['reply_to'],
                                    body=render_response.encode('utf-8'))
        LOGGER.info('[basic_publish] %r', render_response)

    def _submit_process_pool(self):
        self._render_request_q = Queue.Queue(self._config['render_request_q_maxsize'])
        self._render_result_q = Queue.Queue(self._config['render_result_q_maxsize'])
        render_work = RenderWork(handler=do_real_work,
                                 render_request_q=self._render_request_q,
                                 render_result_q=self._render_result_q)
        with concurrent.futures.ProcessPoolExecutor() as ppexecutor:
            for i in range(self._config['render_process_count']):
                res_future = ppexecutor.submit(render_processing, render_work)
                self._render_res_futures.add(res_future)
                LOGGER.info('[create process] %r | %r | %r | %r',
                            i, res_future, self._render_res_futures, render_work)

    def _pull_render_request(self):
        if self._render_request_q.full():
            return
        render_request = self._basic_get_render_request()
        queue_put_nowait(self._render_request_q, render_request)

    def _process_render_result(self):
        render_result = queue_get_nowait(self._render_result_q)
        if render_result is not None:
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
        self._config['render_process_count'] = 2
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

    def stop(self):
        """To do
        """
        LOGGER.info('[stop]')
        self._closing = True
        if self._channel is not None and self._channel.is_open:
            self._channel.close()
            self._channel = None
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
            self._connection = None

    def run(self):
        """To do
        """
        LOGGER.info('[run] %r', os.getpid())
        self._connect()
        self._submit_process_pool()
        LOGGER.info('[start processing]')
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
