# aiopulse2

## Asynchronous library to control Rollease Acmeda Automate roller blinds with the Pulse v2 Hub

This is an updated fork of [aiopulse](https://github.com/atmurray/aiopulse/) for the v2 hub (note: this is _not_ compatible with the v1 hub, use `aiopulse` for that). The protocol implementation uses a combination of WebSockets and a TCP connection using a serial like protocol. See the project wiki page for details.

Requires Python 3.7 or later and uses asyncio and [websockets](https://pypi.org/project/websockets/).

It has been primarily developed as an integration for [Home Assistant](https://www.home-assistant.io/).

### Installing

Run `pip install aiopulse2`.

### Demo.py

This is an interactive interface to test the integration. The available commands are listed below.

Use the `list` command to get the id of the hubs/blinds.

| Command                              | Description                                                                                                        |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| connect [hub ip][hub ip]...]         | Connect to the hub at ip(s)                                                                                        |
| disconnect                           | Disconnect all hubs                                                                                                |
| list                                 | List currently connected hubs and their blinds, use to get the [hub id] and [blind id] for the following commands. |
| open [hub id][blind id]              | Open blind                                                                                                         |
| close [hub id][blind id]             | Close blind                                                                                                        |
| stop [hub id][blind id]              | Stop blind                                                                                                         |
| moveto [hub id][blind id] [% closed] | Open blind to percentage                                                                                           |
| exit                                 | Exit program                                                                                                       |

### pulse_hub_cli.py

This is a trivial work-in-progress aiopulse2 command-line-interface wrapper.  It issues a command to a blind given the hub ip address, device name as defined in the *Pulse 2* app and desired percentage closed.  It then waits for the command to complete.

`python3 pulse_hub_cli.py '192.168.1.127' 'Office 1 of 3' 100`

### close.sh

This is an example application of pulse_hub_cli.py.  It closes three blinds in sequence.  In this case, it is useful to close the blinds one at a time because they share a small power supply.

```
python3 pulse_hub_cli.py '192.168.1.127' 'Office 1 of 3' 100
python3 pulse_hub_cli.py '192.168.1.127' 'Office 2 of 3' 100
python3 pulse_hub_cli.py '192.168.1.127' 'Office 3 of 3' 100
```

