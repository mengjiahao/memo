#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""To do
"""
import concurrent.futures
import json
import logging
import time
import pika

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -20s %(funcName) '
              '-30s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

def do_real_work():
    """To do
    """
    json_data = {"status": "OK", "xpath": "c:/output/视频.mov"}
    LOGGER.info('[doing work...] %r', json_data)
    time.sleep(3)
    render_response = json.dumps(json_data, ensure_ascii=False)
    LOGGER.info('[work result] %r', render_response)

class RenderWork(object):
    """To do
    """
    def __init__(self, tag, data, do_work, arrive_time, timeout):
        self.tag = tag
        self.data = data
        self.do_work = do_work
        self.arrive_time = arrive_time
        self.timeout = timeout

class ExConsumer(object):
    """To do
    """
    def __init__(self):
        self._config = {}
        self._closing = None
        self._connection = None
        self._channel = None
        self._render_pending_reqs = set()
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

    def _render_processing(self, render_work):
        if not isinstance(render_work, RenderWork):
            return None
        render_result = render_work
        render_work.do_work()
        return render_result

    def _on_render_request(self, channel, method_frame, header_frame, body):
        render_request = json.loads(s=body.decode('utf-8'), encoding='utf-8')
        LOGGER.info('[consume] %r | %r | %r | %r', channel, method_frame, header_frame, body)
        render_work = RenderWork(tag=method_frame.delivery_tag,
                                 data=render_request,
                                 do_work=do_real_work,
                                 arrive_time=time.time(),
                                 timeout=self._config['render_work_timeout'])
        with concurrent.futures.ProcessPoolExecutor() as ppexecutor:
            res_future = ppexecutor.submit(self._render_processing, render_work)
            self._render_res_futures.add(res_future)
            self._render_pending_reqs.add(res_future)
        LOGGER.info('[add to pool] %r | %r | %r', render_request, render_work, res_future)

    def _basic_consume_render_request(self):
        self._channel.basic_qos(prefetch_size=0, prefetch_count=1, all_channels=False)
        self._channel.basic_consume(consumer_callback=self._on_render_request,
                                    queue=self._config['render_request_q'],
                                    no_ack=False,
                                    exclusive=False,
                                    consumer_tag=None,
                                    arguments=None)
        LOGGER.info('[basic_consume]')

    def _basic_ack_render_request(self, tag):
        self._channel.basic_ack(delivery_tag=tag, multiple=False)
        LOGGER.info('[basic_ack]')

    def _basic_publish_render_response(self, render_response):
        self._channel.basic_publish(exchange=self._config['render_ex'],
                                    routing_key=render_response['reply_to'],
                                    body=render_response.encode('utf-8'))
        LOGGER.info('[basic_publish] %r', render_response)

    def _process_render_result(self):
        done_res_futures = set()
        for res_future in self._render_res_futures:
            if res_future.done():
                done_res_futures.add(res_future)
        for res_future in done_res_futures:
            self._render_res_futures.remove(res_future)
        for res_future in done_res_futures:
            render_result = res_future.result()
            self._basic_ack_render_request(render_result.tag)
            self._basic_publish_render_response(render_result.data)
            self._render_pending_reqs.remove(render_result)

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
        self._config['render_work_timeout'] = 20

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
        LOGGER.info('[run]')
        self._connect()
        self._basic_consume_render_request()
        LOGGER.info('[start processing]')
        try:
            while True:
                self._connection.process_data_events(1) #self._connection.sleep(1)
                self._process_render_result()
        except KeyboardInterrupt:
            LOGGER.exception('[exception]')
        except pika.exceptions.ChannelClosed:
            LOGGER.exception('[exception]')
        except pika.exceptions.ConnectionClosed:
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
