#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""To do
"""
import logging
import pika

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -20s %(funcName) '
              '-30s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

class ExPublisher(object):
    """To do
    """
    SERVER_EXCHANGE = 'server_exchange'
    SERVER_EXCHANGE_TYPE = 'direct'
    RENDER_REQ_QUEUE = 'render_req_queue'
    RENDER_REQ_ROUTING_KEY = 'render_req_routing_key'
    RENDER_RES_QUEUE = 'render_res_queue'
    RENDER_RES_ROUTING_KEY = 'render_res_routing_key'

    def __init__(self):
        self._connection = None
        self._channel = None
        self._host = None
        self._port = None
        self._virtual_host = None
        self._user = None
        self._passwd = None
        self._url = None
        self._render_req = None
        self._render_res = None

    def _declare_server_exchange(self):
        self._channel.exchange_declare(exchange=self.SERVER_EXCHANGE,
                                       exchange_type=self.SERVER_EXCHANGE_TYPE,
                                       passive=False,
                                       durable=False,
                                       auto_delete=False,
                                       internal=False,
                                       arguments=None)

    def _declare_render_req_queue(self):
        self._channel.queue_declare(queue=self.RENDER_REQ_QUEUE,
                                    passive=False,
                                    durable=False,
                                    exclusive=False,
                                    auto_delete=False,
                                    arguments=None)

    def _declare_render_res_queue(self):
        self._channel.queue_declare(queue=self.RENDER_RES_QUEUE,
                                    passive=False,
                                    durable=False,
                                    exclusive=False,
                                    auto_delete=False,
                                    arguments=None)

    def _bind_render_req_queue(self):
        self._channel.queue_bind(queue=self.RENDER_REQ_QUEUE,
                                 exchange=self.SERVER_EXCHANGE,
                                 routing_key=self.RENDER_REQ_ROUTING_KEY)

    def _bind_render_res_queue(self):
        self._channel.queue_bind(queue=self.RENDER_RES_QUEUE,
                                 exchange=self.SERVER_EXCHANGE,
                                 routing_key=self.RENDER_RES_ROUTING_KEY)

    def _connect(self):
        LOGGER.info('[connect]')
        cred = pika.PlainCredentials(self._user, self._passwd)
        connect_params = pika.ConnectionParameters(host=self._host,
                                                   port=self._port,
                                                   virtual_host=self._virtual_host,
                                                   credentials=cred)
        self._connection = pika.BlockingConnection(connect_params)
        self._channel = self._connection.channel()
        self._declare_server_exchange()
        self._declare_render_req_queue()
        self._bind_render_req_queue()
        self._declare_render_res_queue()
        self._bind_render_res_queue()

    def setup_with_connect_params(self, host, port, virtual_host, user, passwd):
        """To do
        """
        LOGGER.info('[setup]')
        self._host = host
        self._port = port
        self._virtual_host = virtual_host
        self._user = user
        self._passwd = passwd

    def _res_callback(self, channel, method, properties, body):
        print(" [x] Received %r" % body)
        self._render_res = body

    def run(self):
        """To do
        """
        LOGGER.info('[run]')
        self._connect()
        self._render_req = 'Hellow world!'
        LOGGER.info('[publish]')
        self._channel.basic_publish(exchange=self.SERVER_EXCHANGE,
                                    routing_key=self.RENDER_REQ_ROUTING_KEY,
                                    body=self._render_req)
        LOGGER.info('[consume]')
        self._channel.basic_consume(self._res_callback,
                                    queue=self.RENDER_RES_QUEUE,
                                    no_ack=True)
        self._channel.start_consuming()

    def stop(self):
        """To do
        """
        LOGGER.info('[stop]')
        LOGGER.info('[stop]')
        if self._channel is not None:
            self._channel.close()
            self._channel = None
        if self._connection is not None:
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
                                 user='guest',
                                 passwd='guest')
    try:
        ex.run()
        ex.stop()
    except KeyboardInterrupt:
        ex.stop()

if __name__ == '__main__':
    main()
