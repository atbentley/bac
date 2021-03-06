'''
bac
bge android controller

See readme for usage and examples folder for implementation specifics.
'''

import json
import socket
import time


SERVER_PORT = 5558  # 0 = any free socket
BROADCAST_PORT = 38401  # if you change this be sure to change the android app
BROADCAST_DELAY = 1.0  # seconds between broadcasts
DEVICE_LIMIT = -1  # -1 = inf

VERSION = 1  # don't change this
ENCODING = 'UTF-8'  # how to encode/decode data coming in/out of sockets
DEBUG = True  # logs to console when True, is silent when False


# Logging
log = lambda msg: print(msg) if DEBUG else None


class Server:
    '''
    The main component to the bac. Handles the connecting and disconnecting of
    different devices as well as devices requesting to fill a slot and devices
    relinquishing their hold on a slot.
    '''
    def __init__(self, name, local=False):
        '''
        name: the name of the server, is sent out in broadcasts
        local: if True only internal connections will be accepted
        '''
        self.name = name

        self.slots = []
        self.devices = []

        # Initialise server socket (TCP)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = '127.0.0.1' if local else socket.gethostname()
        self.socket.bind((address, SERVER_PORT))
        self.socket.setblocking(False)
        self.socket.listen(5)

        # Initialise broadcast socket (UDP)
        self.broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        self.last_broadcast = 0
        self.broadcast_msg = bytes(json.dumps({
            'bac': VERSION,
            'name': self.name,
            'address': self.socket.getsockname()[0],
            'port': self.socket.getsockname()[1]
        }), 'UTF-8')

    def add_slot(self, name):
        '''Create a new slot'''
        slot = Slot(name)
        self.slots.append(slot)
        return slot

    def request_slot(self, device, slot):
        '''Fill a particular slot with a device if that slot is available'''
        if self.slots[slot].device is None and device.slot is None:
            self.slots[slot].device = device
            device.slot = self.slots[slot]
            return True
        else:
            return False

    def relinquish_slot(self, device):
        '''Remove a device from whatever slot is holds'''
        if device.slot and device.slot.device == device:
            device.slot.device = None
        device.slot = None

    def add_device(self, connection, address, port):
        '''Accept a new device connecting to the server'''
        device = Device(self, connection, address, port)
        self.devices.append(device)
        log('[C] {}'.format(address))

    def remove_device(self, device):
        '''Remove a device from the server'''
        if device.slot is not None:
            self.relinquish_slot(device)
        self.devices.remove(device)
        log('[D] {}'.format(device.address))

    def send_broadcast(self):
        '''Send a UDP broadcast containing the address and port of the server'''
        self.broadcast.sendto(self.broadcast_msg,
            ('255.255.255.255', BROADCAST_PORT))
        self.last_broadcast = time.time()

    def process(self):
        '''Process incoming connections then process connected devices'''
        if time.time() - self.last_broadcast > BROADCAST_DELAY:
            # Time to send a new broadcast.
            self.send_broadcast()            

        try:
            # Check if there are any new connections
            conn, (addr, port) = self.socket.accept()
            self.add_device(conn, addr, port)
        except socket.error:
            # Expected exception, no waiting connection
            pass

        for device in self.devices:
            # Check if there is any incoming data from any of the devices
            device.process()



class Slot:
    '''
    Slots allow more than one device to be giving input at a time. Think of
    these like player slots; player 1 has a slot and player 2 also has a slot.

    Each slot has an associated device (or no device if the slot hasn't been
    filled). Only devices that are in a slot can provide input. Only one device
    may fill a slot at any given time, however if one device relinquishes its
    hold on a slot another device may fill that slot.
    '''
    def __init__(self, name):
        self.name = name

        self.device = None

    def __getattr__(self, attr):
        if self.device:
            if attr is self.device.peripherals:
                return self.device.peripherals[attr]
            else:
                raise AttributeError("Device has no peripheral '{}'").format(
                    attr)


class Device:
    '''
    A representation of an Android device. Contains all the code for managing
    the communication between the device and the server.
    '''
    def __init__(self, server, connection, address, port):
        self.server = server
        self.connection = connection
        self.address = address
        self.port = port

        self.slot = None
        self.buffer = ''

        self.commands = {
            'get_slots': self.process_get_slots,
            'request_slot': self.process_request_slot,
            'relinquish_slot': self.process_relinquish_slot,
            'update_peripherals': self.process_update_peripherals
        }

        self.peripherals = {
            'touch_points': None
        }

    def send(self, msg):
        '''Send a message through the socket'''
        log('[<-] {}: {} {}'.format(self.address, msg['response'],
            json.dumps(msg['args'], sort_keys=True)))
        msg = json.dumps(msg)
        self.connection.send(bytes(msg, ENCODING))

    def process_get_slots(self):
        '''Get the slots' names and availability'''
        msg = {'bac' : 1,
            'response': 'get_slots',
            'args': [{
                'slot': i,
                'name': slot.name,
                'available': slot.device is None
            } for i, slot in enumerate(self.server.slots)]
        }
        self.send(msg)

    def process_request_slot(self, slot):
        '''Request to hold a slot'''
        msg = {
            'bac': 1,
            'response': 'request_slot',
            'args': [self.server.request_slot(self, slot)]
        }
        self.send(msg)

    def process_relinquish_slot(self):
        '''Relinquish a hold on a slot, no return message needed'''
        if self.slot is not None:
            self.server.relinquish_slot(self)

    def process_update_peripherals(self, properties):
        '''Provide an update on the state of different peripherals'''
        if self.slot is not None:
            for peripheral, value in properties.items():
                if peripheral in self.peripherals:
                    self.peripherals[peripheral] = value

    def process_command(self, data):
        '''Determine which command should be run'''
        if data !='':
            try:
                data = json.loads(data)
            except ValueError:
                return

            if isinstance(data, dict):
                if data.get('bac') == VERSION:
                    command = data.get('command')
                    func = self.commands.get(command)
                    if func:
                        args = data.get('args', [])
                        log('[->] {}: {} {}'.format(self.address, command, args))
                        func(*args)
                else:
                    log('[E] {} sent wrong version number'.format(self.address))

    def process(self):
        '''Process any data incoming from device'''
        try:
            data = self.connection.recv(4096).decode(ENCODING)

            if not data:
                # socket closed, removing device also relinquishes slot
                self.connection.close()
                self.server.remove_device(self)
                return

            if self.buffer:
                # Prepend any buffer left over from earlier
                data = self.buffer + data
                self.buffer = ''

            while data:
                # Ignore any characters before opening brace
                data = data[data.index('{'):]

                # Find matching closing brace
                brackets = 0
                for end, char in enumerate(data):
                    if char == '{':
                        brackets += 1
                    elif char == '}':
                        brackets -= 1
                    if brackets == 0:
                        # Closing brace has been found
                        break
                else:
                    # Closing brace wasn't found, append data to buffer
                    self.buffer = data
                    break

                self.process_command(data[:end+1])
                data = data[end+2:]

        except socket.error:
            # There wasn't any data waiting in the socket, continue on
            pass
        except ValueError:
            # data did not have opening brace ({), data was not proper json
            pass


if __name__ == "__main__":
    # Setup a quick server for testing
    server = Server('Test Server')
    server.add_slot('Slot 1')
    server.add_slot('Slot 2')
    while True:
        server.process()
