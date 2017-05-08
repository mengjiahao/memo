#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""To do
"""
import json
import logging
import time
import pika

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -20s %(funcName) '
              '-30s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

class ExConsumer(object):
    """To do
    """
    def __init__(self):
        self._config = {}
        self._config['render_ex'] = 'render_ex'
        self._config['render_ex_type'] = 'direct'
        self._config['render_request_q'] = 'render_request_q'
        self._config['render_request_rk'] = 'render_request_rk'
        self._config['render_response_q'] = 'render_response_q'
        self._config['render_response_rk'] = 'render_response_rk'
        self._config['host'] = 'localhost'
        self._config['port'] = 'port'
        self._config['virtual_host'] = '/'
        self._config['username'] = 'guest'
        self._config['password'] = 'guest'
        self._closing = None
        self._connection = None
        self._channel = None
        self._render_request = None
        self._render_response = None
        self._render_reply_to = None

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

    def _get_render_request(self):
        (method_frame, header_frame, body) = \
            self._channel.basic_get(queue=self._config['render_request_q'], no_ack=True)
        if (method_frame is not None) and (header_frame is not None) and (body is not None):
            self._render_request = json.loads(s=body.decode('utf-8'), encoding='utf-8')
            self._render_reply_to = self._render_request['reply_to']
            LOGGER.info('[get] %r', self._render_request)
            return True
        return False

    def _do_work(self):
        json_data = {"status": "OK", "xpath": "c:/output/视频.mov"}
        LOGGER.info('[doing work...] %r', json_data)
        time.sleep(3)
        self._render_response = json.dumps(json_data, ensure_ascii=False)
        LOGGER.info('[work result] %r', self._render_response)

    def _publish_render_response(self):
        self._channel.basic_publish(exchange=self._config['render_ex'],
                                    routing_key=self._render_reply_to,
                                    body=self._render_response.encode('utf-8'))
        LOGGER.info('[publish] %r', self._render_response)

    def setup_with_connect_params(self, host, port, virtual_host, username, password):
        """To do
        """
        LOGGER.info('[setup]')
        self._config['host'] = host
        self._config['port'] = port
        self._config['virtual_host'] = virtual_host
        self._config['username'] = username
        self._config['password'] = password

    def run(self):
        """To do
        """
        LOGGER.info('[run]')
        self._connect()
        self._closing = False
        while not self._closing:
            if self._get_render_request():
                self._do_work()
                self._publish_render_response()

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

def main():
    """To do
    """
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    ex = ExConsumer()
    ex.setup_with_connect_params(host='localhost',
                                 port=5672,
                                 virtual_host='/',
                                 username='guest',
                                 password='guest')
    try:
        ex.run()
    except KeyboardInterrupt:
        LOGGER.exception('[exception]')
        ex.stop()

if __name__ == '__main__':
    main()
