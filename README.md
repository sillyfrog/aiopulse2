# Aiopulse 2

## Asynchronous library to control Rollease Acmeda Automate roller blinds with the Pulse v2 Hub

This is an updated fork of https://github.com/atmurray/aiopulse/

Requires Python 3 and uses asyncio.

### Installing
I plan on publishing this module to PiPy once I'm happy that it has been adequately tested.
For now, from the folder containing setup.py run `python setup.py install`.

### Demo.py commands:
| Command                               | Description               |
|---------------------------------------|---------------------------|
|discover                               | Find and connect to any hubs on the local network (uses udp broadcast discovery)|
|connect                                | Connect to all hubs and trigger update|
|disconnect                             | Disconnect all hubs|
|update                                 | Refresh all information from hub|
|list                                   | List currently connected hubs and their blinds, use to get the [hub id] and [blind id] for the following commands.|
|open [hub id] [blind id]               | Open blind|
|close [hub id] [blind id]              | Close blind|
|stop [hub id] [blind id]               | Stop blind|
|moveto [hub id] [blind id] [% closed]  | Open blind to percentage|
|exit                                   | Exit program|
