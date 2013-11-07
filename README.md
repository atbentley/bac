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

License
---
The MIT License (MIT)

Copyright (c) 2013 Andrew

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
