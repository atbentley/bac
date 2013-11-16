BGE Android Controller
===

The bac allows Android devices to be used as controllers for your PC game. While intended to be used for the Blender game engine, bac has no game engine dependent code and should run in any python 3 environment. 

Usage
---

First, initialise the bac server
````python
import bac

# Create server
server = bac.Server('Test Server')

# Create a slot for each player
slot1 = server.add_slot('Slot 1')
slot2 = server.add_slot('Slot 2')
````

Update the server on each logic tick (bac is non-blocking and single threaded)
````python
server.process()
````

Get some input from the device peripherals
````python
# Get some input from the devices
print(slot1.touch_points)

# Alternatively, you don't need to maintain a reference to the slots
print(server.slots[0].touch_points)
````