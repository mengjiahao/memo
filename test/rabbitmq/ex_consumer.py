#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""To do
"""
import logging
import time
import pika

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -20s %(funcName) '
              '-30s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

class ExConsumer(object):
    """To do
    """
    SERVER_EXCHANGE = 'server_exchange'
    SERVER_EXCHANGE_TYPE = 'direct'
    RENDER_REQ_QUEUE = 'render_req_queue'
    RENDER_REQ_ROUTING_KEY = 'render_req_routing_key'
    RENDER_RES_QUEUE = 'render_res_queue'
    RENDER_RES_ROUTING_KEY = 'render_res_routing_key'
    STATE_INVALID = 0
    STATE_IDLE = 1
    STATE_RENDERING = 2
    STATE_PUBLISH_RENDER_RES = 3

    def __init__(self):
        self._closing = True
        self._connection = None
        self._channel = None
        self._state = self.STATE_INVALID
        self._host = None
        self._port = None
        self._virtual_host = None
        self._user = None
        self._passwd = None
        self._url = None
        self._render_req = None
        self._render_res = None

    def _change_state(self, state):
        LOGGER.info('[change state %d -> %d]', self._state, state)
        self._state = state

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

    def _bind_render_req_queue(self):
        self._channel.queue_bind(queue=self.RENDER_REQ_QUEUE,
                                 exchange=self.SERVER_EXCHANGE,
                                 routing_key=self.RENDER_REQ_ROUTING_KEY)

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

    def _reconnect(self):
        LOGGER.info('[reconnect]')
        if not self._closing:
            # Create a new connection
            self._connect()

    def _consume_render_req(self):
        method_frame, header_frame, body = self._channel.basic_get(queue=self.RENDER_REQ_QUEUE,
                                                                   no_ack=True)
        if (method_frame is not None) and (header_frame is not None) and (body is not None):
            LOGGER.info('[consume] %r', body)
            self._render_req = body
            return True
        return False

    def _rendering(self):
        LOGGER.info('[rendering begin]')
        time.sleep(5)
        self._render_res = 'It is OK!'
        LOGGER.info('[rendering end]')
        return True

    def _publish_render_res(self):
        LOGGER.info('[publish] %r', self._render_res)
        self._channel.basic_publish(exchange=self.SERVER_EXCHANGE,
                                    routing_key=self.RENDER_RES_ROUTING_KEY,
                                    body=self._render_res)
        return True

    def setup_with_connect_params(self, host, port, virtual_host, user, passwd):
        """To do
        """
        LOGGER.info('[setup]')
        self._host = host
        self._port = port
        self._virtual_host = virtual_host
        self._user = user
        self._passwd = passwd

    def run(self):
        """To do
        """
        LOGGER.info('[run]')
        self._connect()
        self._closing = False
        self._change_state(self.STATE_IDLE)
        while not self._closing:
            if self.STATE_IDLE == self._state:
                if self._consume_render_req():
                    self._change_state(self.STATE_RENDERING)
            elif self.STATE_RENDERING == self._state:
                if self._rendering():
                    self._change_state(self.STATE_PUBLISH_RENDER_RES)
            elif self.STATE_PUBLISH_RENDER_RES == self._state:
                if self._publish_render_res():
                    self._change_state(self.STATE_IDLE)
            else:
                LOGGER.warning('self._state %d is invalid', self._state)
                break

    def stop(self):
        """To do
        """
        LOGGER.info('[stop]')
        self._closing = True
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
    ex = ExConsumer()
    ex.setup_with_connect_params(host='localhost',
                                 port=5672,
                                 virtual_host='/',
                                 user='guest',
                                 passwd='guest')
    try:
        ex.run()
    except KeyboardInterrupt:
        ex.stop()

if __name__ == '__main__':
    main()
