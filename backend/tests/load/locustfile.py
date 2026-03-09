"""压测入口 — python -m tests.load.locustfile"""

from tests.load import main

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
