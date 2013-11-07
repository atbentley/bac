'''
bac tester.

This works by running a number of scenarios and catching the log output and
comparing it to a successful log.
'''

import json
import socket
import traceback
import time

import bac


class TestError(Exception):
    pass


def find_server():
    '''Locate a bac server'''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', bac.BROADCAST_PORT))

    while True:
        data = s.recv(1024).decode(bac.ENCODING)
        try:
            data = json.loads(data)
        except ValueError:
            pass

        if isinstance(data, dict) and data.get('bac') == bac.VERSION:
            addr = data.get('address')
            port = data.get('port')
            return addr, port


def send(socket, msg):
    '''Send a message through a socket'''
    msg = json.dumps(msg) + "\n"
    socket.send(bytes(msg, bac.ENCODING))


def recv(socket):
    '''Recieve a message from a socket'''
    data = socket.recv(4096).decode(bac.ENCODING)
    return data


class log:
    '''This logger compares incoming logs with those from a success log file.'''
    def __init__(self):
        with open('successful.txt', 'r') as f:
            self.lines = f.readlines()

    def __call__(self, c):
        line = self.lines.pop(0)[:-1]
        if not line == '{}'.format(c):
            stack = traceback.extract_stack()
            for l in traceback.format_list(stack[:-4]):
                print(l[:-1])
            print('Expected: "{}"'.format(line))
            print('Got:      "{}"'.format(c))
            raise TestError


class log2:
    '''This logger writes logs to a file ot be used a success log file.'''
    def __init__(self):
        self.f = open('successful.txt', 'w')
        self.f.truncate(0)

    def __call__(self, c):
        msg = "{}".format(c)
        print(msg)
        self.f.write(msg + "\n")


def test(write=False):
    if write:
        bac.log = log2()
    else:
        bac.log = log()    

    # Initialise server
    server = bac.Server('Test Server', local=True)
    s1 = server.add_slot('Slot 1')
    s2 = server.add_slot('Slot 2')

    addr = '127.0.0.1'
    port = server.socket.getsockname()[1]

    # Create sockets and connect to server
    socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket1.connect((addr, port))
    time.sleep(0.1)
    server.process()

    socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket2.connect((addr, port))
    time.sleep(0.1)
    server.process()

    socket3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket3.connect((addr, port))
    time.sleep(0.1)
    server.process()

    # Wrong version number
    send(socket1, {'bac': bac.VERSION+1})
    time.sleep(0.1)
    server.process()
    #recv(socket1)

    # Get slots
    send(socket1, {'bac': bac.VERSION, 'command': 'get_slots'})
    time.sleep(0.1)
    server.process()
    #recv(socket1)

    # Request slot
    send(socket1, {'bac': bac.VERSION, 'command': 'request_slot', 'args': [0]})
    time.sleep(0.1)
    server.process()
    #recv(socket1)

    # Get slots
    send(socket2, {'bac': bac.VERSION, 'command': 'get_slots'})
    time.sleep(0.1)
    server.process()
    #recv(socket2)

    # Request occupied slot
    send(socket2, {'bac': bac.VERSION, 'command': 'request_slot', 'args': [0]})
    time.sleep(0.1)
    server.process()
    #recv(socket2)

    # Relinquish slot
    send(socket1, {'bac': bac.VERSION, 'command': 'relinquish_slot'})
    time.sleep(0.1)
    server.process()
    #recv(socket1)

    # Get slots
    send(socket3, {'bac': bac.VERSION, 'command': 'get_slots'})
    time.sleep(0.1)
    server.process()
    #recv(socket3)

    # Request slot
    send(socket1, {'bac': bac.VERSION, 'command': 'request_slot', 'args': [0]})
    time.sleep(0.1)
    server.process()
    #recv(socket1)

    # Request slot
    send(socket2, {'bac': bac.VERSION, 'command': 'request_slot', 'args': [1]})
    time.sleep(0.1)
    server.process()
    #recv(socket2)

    # Get slots
    send(socket1, {'bac': bac.VERSION, 'command': 'get_slots'})
    time.sleep(0.1)
    server.process()
    #recv(socket1)

    # Disconnect from server
    recv(socket1)
    socket1.close()
    time.sleep(0.1)
    server.process()

    recv(socket2)
    socket2.close()
    time.sleep(0.1)
    server.process()

    recv(socket3)
    socket3.close()
    time.sleep(0.1)
    server.process()

    print('All tests completed successfully!')

if __name__ == '__main__':
    try:
        test(write=False)
    except TestError:
        pass
