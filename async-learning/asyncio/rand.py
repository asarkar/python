"""Demonstrates coroutines - https://realpython.com/async-io-python/"""

import asyncio
import random

# ANSI colors
c = (
    "\033[0m",  # End of color
    "\033[36m",  # Cyan
    "\033[91m",  # Red
    "\033[35m",  # Magenta
)


async def makerandom(idx: int, threshold: int) -> int:
    """Return a randomly generated number greater than the given threshold.

    If a random number if smaller than the threshold, sleep it off and then try again.
    """
    print(c[idx + 1] + f"---> Initiated makerandom({idx}) with threshold: {threshold}.")
    i = random.randint(0, 10)
    while i <= threshold:
        print(c[idx + 1] + f"makerandom({idx}) == {i} too low; retrying.")
        await asyncio.sleep(idx + 1)
        i = random.randint(0, 10)
    print(c[idx + 1] + f"<--- Finished: makerandom({idx}) == {i}" + c[0])
    return i


async def main():
    # Invoke makerandom 3 times, each time decrementing the threshold
    res = await asyncio.gather(*(makerandom(i, 10 - i - 1) for i in range(3)))
    return res


if __name__ == "__main__":
    random.seed(444)
    r1, r2, r3 = asyncio.run(main())
    print()
    print(f"r1: {r1}, r2: {r2}, r3: {r3}")
