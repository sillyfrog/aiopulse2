#!/usr/bin/env python3
"""Demo."""
import asyncio
import logging
import sys

import aiopulse2


async def main():
    hosts = sys.argv[1:]
    if not hosts:
        print("Usage: hubtest.py host1 [host2 ...]")
        return
    for host in hosts:
        try:
            hub = aiopulse2.Hub(host)
            result = await hub.test(True)
            if result:
                print(f"Host: {host}: {hub}")
                for roller in hub.rollers.values():
                    print(f"    {roller}")
            else:
                print(f"Host: {host}: Unknown Error")
        except Exception as e:
            print(f"Host: {host}: Error ({e})")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
