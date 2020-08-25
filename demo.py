#!/usr/bin/env python3
"""Demo."""
import asyncio
import cmd
import functools
import logging
from typing import Any, Callable, Optional

import aiopulse2
from aiopulse2 import _LOGGER


class HubPrompt(cmd.Cmd):
    """Prompt command line class based on cmd."""

    def __init__(self, event_loop):
        """Init command interface."""
        self.hubs = {}
        self.event_loop = event_loop
        self.running = True
        super().__init__()

    def add_job(self, target: Callable[..., Any], *args: Any) -> None:
        """Add job to the executor pool.

        target: target to call.
        args: parameters for method to call.
        """
        if target is None:
            raise ValueError("Don't call add_job with None")
        self.event_loop.call_soon_threadsafe(self.async_add_job, target, *args)

    def async_add_job(
        self, target: Callable[..., Any], *args: Any
    ) -> Optional[asyncio.Future]:
        """Add a job from within the event loop.

        This method must be run in the event loop.

        target: target to call.
        args: parameters for method to call.
        """
        task = None

        # Check for partials to properly determine if coroutine function
        check_target = target
        while isinstance(check_target, functools.partial):
            check_target = check_target.func

        if asyncio.iscoroutine(check_target):
            task = self.event_loop.create_task(target)  # type: ignore
        elif asyncio.iscoroutinefunction(check_target):
            task = self.event_loop.create_task(target(*args))
        else:
            task = self.event_loop.run_in_executor(None, target, *args)  # type: ignore

        return task

    async def add_hub(self, hubip):
        """Add a hub to the prompt."""
        hub = aiopulse2.Hub(hubip)
        self.hubs[hub.id] = hub
        hub.callback_subscribe(self.hub_update_callback)
        await hub.run()
        print("Hub added to prompt")

    async def hub_update_callback(self, hub, update_type):
        """Called when a hub reports that its information is updated."""
        print(f"Hub {hub.name!r}, type {update_type} updated")
        for roller in hub.rollers.values():
            roller.callback_subscribe(self.roller_update_callback)

    async def roller_update_callback(self, roller):
        """Called when a roller reports it has updated"""
        print(f"Roller Updated: {roller}")

    def _get_roller(self, args):
        """Return roller based on string argument."""
        try:
            hub_id = int(args[0]) - 1
            roller_id = int(args[1]) - 1
            return list(list(self.hubs.values())[hub_id].rollers.values())[roller_id]
        except Exception:
            print("Invalid arguments {}".format(args))
            print(
                "Format is <hub index> <roller index>. See 'list' for the index of each device."
            )
            return None

    def do_list(self, args):
        """Command to list all hubs and rollers."""
        print("Listing hubs...")
        hub_id = 0
        for hub in self.hubs.values():
            hub_id += 1
            print(f"Hub {hub_id}: {hub}")
            roller_id = 0
            for roller in hub.rollers.values():
                roller_id += 1
                print(f"Roller {roller_id}: {roller}")

    def do_moveto(self, sargs):
        """Command to tell a roller to move a % closed."""
        print("Sending move to")
        args = sargs.split()
        roller = self._get_roller(args)
        if roller:
            position = int(args[2])
            print("Sending blind move to {}".format(roller.name))
            self.add_job(roller.move_to, position)

    def do_close(self, sargs):
        """Command to close a roller."""
        args = sargs.split()
        roller = self._get_roller(args)
        if roller:
            print("Sending blind down to {}".format(roller.name))
            self.add_job(roller.move_down)

    def do_open(self, sargs):
        """Command to open a roller."""
        args = sargs.split()
        roller = self._get_roller(args)
        if roller:
            print("Sending blind up to {}".format(roller.name))
            self.add_job(roller.move_up)

    def do_stop(self, sargs):
        """Command to stop a moving roller."""
        args = sargs.split()
        roller = self._get_roller(args)
        if roller:
            print("Sending blind stop to {}".format(roller.name))
            self.add_job(roller.move_stop)

    def do_connect(self, sargs):
        """Command to connect all hubs."""
        for hubip in sargs.split():
            print("Hub IP:", hubip)
            if hubip not in self.hubs:
                self.add_job(self.add_hub, hubip)

    def do_disconnect(self, sargs):
        """Command to disconnect all connected hubs."""
        for hub in self.hubs.values():
            self.add_job(hub.stop)

    def do_log(self, sargs):
        """Change logging level."""
        if sargs == "critical":
            _LOGGER.setLevel(logging.CRITICAL)
            print("Log level set to critical")
        elif sargs == "error":
            _LOGGER.setLevel(logging.ERROR)
            print("Log level set to error")
        elif sargs == "warning":
            _LOGGER.setLevel(logging.WARNING)
            print("Log level set to warning")
        elif sargs == "info":
            _LOGGER.setLevel(logging.INFO)
            print("Log level set to info")
        elif sargs == "debug":
            _LOGGER.setLevel(logging.DEBUG)
            print("Log level set to debug")
        else:
            print("Valid log levels are critical, error, warning, info, and debug.")

    def do_exit(self, arg):
        """Command to exit."""
        print("Exiting")
        self.running = False
        for hub in self.hubs.values():
            self.async_add_job(hub.stop())
        return True


async def main():
    """Test code."""
    event_loop = asyncio.get_running_loop()

    prompt = HubPrompt(event_loop)
    prompt.prompt = "> "

    tasks = [event_loop.run_in_executor(None, prompt.cmdloop)]

    await asyncio.wait(tasks)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
