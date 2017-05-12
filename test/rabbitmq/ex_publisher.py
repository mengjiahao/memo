#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""To do
"""
import os
import sys
import getopt
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

class ExPublisher(object):
    """To do
    """
    def __init__(self):
        self._config = {}
        self._closing = None
        self._connection = None
        self._channel = None
        self._render_request = None
        self._render_response = None
        self._delivery_tag = None

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
        self._channel.queue_declare(queue=self._config['render_response_q'],
                                    passive=False,
                                    durable=False,
                                    exclusive=False,
                                    auto_delete=False,
                                    arguments=None)
        self._channel.queue_bind(queue=self._config['render_request_q'],
                                 exchange=self._config['render_ex'],
                                 routing_key=self._config['render_request_rk'])
        self._channel.queue_bind(queue=self._config['render_response_q'],
                                 exchange=self._config['render_ex'],
                                 routing_key=self._config['render_response_rk'])

    def _connect(self):
        cred = pika.PlainCredentials(self._config['username'],
                                     self._config['password'])
        connect_params = pika.ConnectionParameters(self._config['host'],
                                                   self._config['port'],
                                                   virtual_host=self._config['virtual_host'],
                                                   credentials=cred)
        self._connection = pika.BlockingConnection(connect_params)
        self._channel = self._connection.channel()
        self._build_render_ex_and_q()
        LOGGER.info('[connect]')

    def _on_render_response(self, channel, method_frame, header_frame, body):
        self._render_response = json.loads(s=body.decode('utf-8'), encoding='utf-8')
        logging.info("[received] %r", self._render_response)

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

    def configure(self, options=None):
        """To do
        """
        self._default_config()
        LOGGER.info('[config] %r', self._config)

    def _stop(self):
        LOGGER.info('[stop]')
        self._closing = True
        if self._channel is not None and self._channel.is_open:
            self._channel.close()
            self._channel = None
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
            self._connection = None

    def _get_json_data(self):
        json_data = {"status": "UnKnown", "reply_to": self._config['render_response_rk'],
                     "xpath": "c:/footage/文件名.aepx"}
        return json_data

    def start(self):
        """To do
        """
        LOGGER.info('[running]')
        self._connect()
        self._channel.basic_consume(consumer_callback=self._on_render_response,
                                    queue=self._config['render_response_q'],
                                    no_ack=True,
                                    exclusive=False,
                                    consumer_tag=None,
                                    arguments=None)

        json_data = self._get_json_data()
        self._render_request = json.dumps(obj=json_data, ensure_ascii=False)
        logging.info("[create request] %r", self._render_request)

        pb_result = self._channel.basic_publish(exchange=self._config['render_ex'],
                                                routing_key=self._config['render_request_rk'],
                                                body=self._render_request.encode('utf-8'))
        LOGGER.info('[publish] pb_result: %r', pb_result)
        LOGGER.info('[start consuming]')
        try:
            self._channel.start_consuming()
        except KeyboardInterrupt:
            self._channel.stop_consuming()
        self._stop()

    def _on_test_message(self, channel, method_frame, header_frame, body):
        logging.info("[received] body: %r", body)
        time.sleep(10)
        self._delivery_tag = method_frame.delivery_tag
        self._channel.basic_ack(delivery_tag=self._delivery_tag, multiple=False)
        logging.info("[basic_ack] delivery_tag: %r", self._delivery_tag)

    def test_rabbitmq(self):
        """To do
        """
        LOGGER.info('[test rabbitmq]')
        self._connect()
        self._channel.basic_qos(prefetch_size=0, prefetch_count=1, all_channels=False)
        self._channel.basic_consume(consumer_callback=self._on_test_message,
                                    queue=self._config['render_response_q'],
                                    no_ack=True,
                                    exclusive=False,
                                    consumer_tag=None,
                                    arguments=None)

        json_data = {"reply_to": self._config['render_response_rk'], "xpath": "c:/footage/文件名.aepx"}
        self._render_request = json.dumps(obj=json_data, ensure_ascii=False)
        logging.info("[create req] %r", self._render_request)

        pb_result = self._channel.basic_publish(exchange=self._config['render_ex'],
                                                routing_key=self._config['render_response_rk'],
                                                body=self._render_request.encode('utf-8'))
        LOGGER.info('[publish 1] %r', pb_result)
        pb_result = self._channel.basic_publish(exchange=self._config['render_ex'],
                                                routing_key=self._config['render_response_rk'],
                                                body=self._render_request.encode('utf-8'))
        LOGGER.info('[publish 2] %r', pb_result)
        LOGGER.info('[start consuming]')
        try:
            self._channel.start_consuming()
        except KeyboardInterrupt:
            self._channel.stop_consuming()
        self.stop()

    def _test_processing(self):
        """To do
        """
        print('[work_process start] time: %f, pid: %d, ppid: %d' %
              (time.time(), os.getpid(), os.getppid()))
        time.sleep(2)
        json_data = {"tx_id": 1, "status": "正常"}
        print('[work_process end] time: %f, pid: %d, ppid: %d, '
              'json_data: %r, is_dict: %d, size: %d' %
              (time.time(), os.getpid(), os.getppid(), json_data,
               isinstance(json_data, dict), sys.getsizeof(json_data)))
        return json_data

    def test_process_pool(self):
        """To do
        """
        LOGGER.info('[main_process start] pid: %r, ppid: %r', os.getpid(), os.getppid())
        res_futures = set()
        ppexecutor = concurrent.futures.ProcessPoolExecutor(max_workers=1)
        for i in range(3):
            res_future = ppexecutor.submit(self._test_processing)
            res_futures.add(res_future)
            LOGGER.info('[submit process] i: %r, res_future: %r, res_futures: %r',
                        i, res_future, res_futures)
        LOGGER.info('[main_process continue] pid: %r, ppid: %r', os.getpid(), os.getppid())
        for i in range(6):
            LOGGER.info('[monitor] res_futures: %r', res_futures)
            remove_set = set()
            for res_future in res_futures:
                if res_future.done():
                    LOGGER.info('[result] result: %r', res_future.result())
                    remove_set.add(res_future)
            for res_future in remove_set:
                res_futures.remove(res_future)
            time.sleep(2)
        ppexecutor.shutdown()
        LOGGER.info('[main_process end] pid: %r, ppid: %r', os.getpid(), os.getppid())

def logging_config():
    """To do
    """
    logging.basicConfig(level=logging.INFO,
                        format=LOG_FORMAT,
                        #filename='logs/ae_publish.log',
                        #filemode='a+'
                        )
    #console = logging.StreamHandler()
    #console.setLevel(logging.INFO)
    #logging.getLogger('').addHandler(console)

def main():
    """To do
    """
    logging_config()
    LOGGER.info('*************************************************')
    LOGGER.info('*               ae rabbitmq publisher           *')
    LOGGER.info('*************************************************')
    ex = ExPublisher()
    ex.configure()
    ex.start()

if __name__ == '__main__':
    main()
