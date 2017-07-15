# Assignment
1. Ping service: Answer a ping request.
2. Hash service: The server will receive as input a text from a client. This
service calculates a hash value for the determined text with the function:
hash = (hash + char) % 1000000000
The hash obtained is returned to the client as an integer value.

## Requirements
1. Need install portmap.
2. use /etc/init.d/rpcbind {start|stop|force-reload|restart|status}

## Test
1. Ping service: (1) ./server; (2) ./client -s 127.0.1.1; c> ping
2. Hash service: (1) ./server; (2) ./client -s 127.0.1.1; c> hash 1.txt
 