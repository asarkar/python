"""Demonstrates producing and consuming items asynchronously using a queue - https://realpython.com/async-io-python/"""

import asyncio
import os
import random
import time


async def makeitem(size: int = 5) -> str:
    """Return a random string."""
    return os.urandom(size).hex()


async def randsleep(caller=None) -> None:
    """Sleep for a random time."""
    i = random.randint(0, 10)
    if caller:
        print(f"{caller} sleeping for {i} seconds.")
    await asyncio.sleep(i)


async def produce(name: int, q: asyncio.Queue) -> None:
    """Put a random number of items in the queue."""
    n = random.randint(0, 10)
    for k in range(1, n + 1):  # Synchronous loop for each single producer
        await randsleep(caller=f"Producer {name}")
        i = await makeitem()
        t = time.perf_counter()
        await q.put((i, t))
        print(f"Producer {name} added <{i}> to queue; {n - k} more items to go.")


async def consume(name: int, q: asyncio.Queue) -> None:
    while True:
        await randsleep(caller=f"Consumer {name}")
        i, t = await q.get()
        now = time.perf_counter()
        print(f"Consumer {name} got element <{i}>"
              f" in {now - t:0.5f} seconds.")
        q.task_done()


async def main(nprod: int, ncon: int):
    q = asyncio.Queue()
    producers = [asyncio.create_task(produce(n, q)) for n in range(nprod)]
    consumers = [asyncio.create_task(consume(n, q)) for n in range(ncon)]
    await asyncio.gather(*producers)
    # the key is to await q.join(), which blocks until all items in the queue have been received and processed,
    # and then to cancel the consumer tasks, which would otherwise hang up and wait endlessly for additional queue
    # items to appear
    await q.join()
    for c in consumers:
        c.cancel()


if __name__ == "__main__":
    import argparse

    random.seed(444)
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--nprod", type=int, default=5)
    parser.add_argument("-c", "--ncon", type=int, default=10)
    ns = parser.parse_args()
    start = time.perf_counter()
    asyncio.run(main(**ns.__dict__))
    elapsed = time.perf_counter() - start
    print(f"Program completed in {elapsed:0.5f} seconds.")
