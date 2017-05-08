#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""To do
"""
import json
import logging
import pika

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -20s %(funcName) '
              '-30s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

class ExPublisher(object):
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

    def setup_with_connect_params(self, host, port, virtual_host, username, password):
        """To do
        """
        LOGGER.info('[setup]')
        self._config['host'] = host
        self._config['port'] = port
        self._config['virtual_host'] = virtual_host
        self._config['username'] = username
        self._config['password'] = password

    def _gen_json_data(self):
        json_data = {"reply_to": self._config['render_response_rk'], "xpath": "c:/footage/文件名.aepx"}
        self._render_request = json.dumps(obj=json_data, ensure_ascii=False)
        logging.info("[gen req] %r", self._render_request)

    def _on_render_response(self, channel, method_frame, header_frame, body):
        self._render_response = json.loads(s=body.decode('utf-8'), encoding='utf-8')
        logging.info("[received] %r", self._render_response)

    def run(self):
        """To do
        """
        LOGGER.info('[run]')
        self._connect()
        self._channel.basic_consume(consumer_callback=self._on_render_response,
                                    queue=self._config['render_response_q'],
                                    no_ack=True,
                                    exclusive=False,
                                    consumer_tag=None,
                                    arguments=None)
        self._gen_json_data()
        pb_result = self._channel.basic_publish(exchange=self._config['render_ex'],
                                                routing_key=self._config['render_request_rk'],
                                                body=self._render_request.encode('utf-8'))
        LOGGER.info('[publish] %r', pb_result)
        LOGGER.info('[start consuming]')
        try:
            self._channel.start_consuming()
        except KeyboardInterrupt:
            self._channel.stop_consuming()

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
    ex = ExPublisher()
    ex.setup_with_connect_params(host='localhost',
                                 port=5672,
                                 virtual_host='/',
                                 username='guest',
                                 password='guest')
    ex.run()
    ex.stop()

if __name__ == '__main__':
    main()
