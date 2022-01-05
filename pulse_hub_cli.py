#!/usr/bin/env python3
"""cli utility"""
import asyncio
import functools
from typing import Any, Callable, Optional
import aiopulse2
import sys

def add_job(event_loop, target: Callable[..., Any], *args: Any) -> None:
    """Add job to the executor pool.
    target: target to call.
    args: parameters for method to call.
    """
    if target is None:
        raise ValueError("Don't call add_job with None")
    event_loop.call_soon_threadsafe(async_add_job, event_loop, target, *args)

def async_add_job(
    event_loop, target: Callable[..., Any], *args: Any
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
        task = event_loop.create_task(target)  # type: ignore
    elif asyncio.iscoroutinefunction(check_target):
        task = event_loop.create_task(target(*args))
    else:
        task = event_loop.run_in_executor(None, target, *args)  # type: ignore
    return task

async def main():
  """cli utility"""

  if(len(sys.argv) != 4):
    raise ValueError("usage: pulse_hub_cli.py hub_ip roller_name closed_percent\n")

  hubip=sys.argv[1]
  desired_roller_name = sys.argv[2]
  desired_closed_percent = int(sys.argv[3])

 # hubip='192.168.1.127'
 # desired_roller_name = 'Office 3 of 3'
 # desired_closed_percent = 26 # 26 (27 for 1 of 3) closed percent is the desired location

  print(f" move hub {hubip} roller {desired_roller_name} to closed {desired_closed_percent}%")

  event_loop = asyncio.get_running_loop()

  print("  setup the hub")
  hub = aiopulse2.Hub(hubip)
  add_job(event_loop, hub.run)
  await hub.rollers_known.wait()

  print("  find the roller")
  for roller in hub.rollers.values():
    if(roller.name==desired_roller_name):
      break
  else:
    print(f"  failed to find roller {desired_roller_name}")
   # to-do sometimes it takes a little while for a roller to come in
    exit(1)

  print("  ensure the roller is all set")
  while(roller.closed_percent==None):
    print(f" roller {roller.name} has not reported yet")
    await asyncio.sleep(0.5)

  print('  send moveto command')
  add_job(event_loop, roller.move_to, desired_closed_percent)

  print(f"  wait for the roller to arrive at {desired_closed_percent}")
  counter=0
  while(roller.closed_percent != desired_closed_percent):
    counter+=1
    if(counter>200): # timeout after 20 seconds - to-do - rounding error can cause this e.g. a roller looking for 27 to finish at 26
      print(f"  timeout - roller has not yet arrived at {desired_closed_percent} - {roller.closed_percent}")
      exit(1)
    await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())