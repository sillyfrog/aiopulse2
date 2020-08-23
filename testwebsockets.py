#!/usr/bin/env python

import asyncio
import ssl
import websockets
import time
import json

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

HOST = "10.1.0.61"
BLIND_ID = "S1S"

# import logging
# logger = logging.getLogger("websockets")
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())


async def getupdates(ws):
    while 1:
        await asyncio.sleep(3)
        qry = {"method": "shadow", "src": "app", "id": int(time.time())}
        print("Sending shadow...")
        await ws.send(json.dumps(qry))


async def moveblind(ws):
    await asyncio.sleep(5)
    # this moves the blind
    qry = {
        "method": "shadow",
        "args": {
            "desired": {"shades": {BLIND_ID: {"movePercent": 85}}},
            "timeStamp": time.time(),
        },
    }
    await ws.send(json.dumps(qry))
    print("Send qry", qry)


async def consumer(msg):
    print("Got back: ", msg)


async def hello():
    uri = "wss://{}:443/rpc".format(HOST)
    async with websockets.connect(uri, ssl=ssl_context) as websocket:

        qry = {
            "method": "shadow",
            "args": {
                "desired": {"shades": {BLIND_ID: {"query": True}}},
                "timeStamp": time.time(),
            },
        }
        await websocket.send(json.dumps(qry))

        asyncio.create_task(getupdates(websocket))
        asyncio.create_task(moveblind(websocket))

        async for message in websocket:
            await consumer(message)

        return

        for i in range(3):
            await asyncio.sleep(5)
            qry = {"method": "shadow", "src": "app", "id": int(time.time())}
            # This never returns a result
            # qry = {
            #     "method": "shadow",
            #     "args": {
            #         "desired": {"shades": {BLIND_ID: {"query": True}}},
            #         "timeStamp": time.time(),
            #     },
            # }
            await websocket.send(json.dumps(qry))
            print("Send qry", qry)
            response = json.loads(await websocket.recv())
            print("Response:")
            print(
                json.dumps(
                    response["result"]["reported"]["shades"][BLIND_ID], indent="  "
                )
            )


asyncio.get_event_loop().run_until_complete(hello())
