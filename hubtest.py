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
            result = await hub.test()
            if result:
                msg = f"OK ({hub.name!r})"
            else:
                msg = "Unknown error"
        except Exception as e:
            msg = f"Error: {e}"
        print(f"Host: {host}: {msg}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
