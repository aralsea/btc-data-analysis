import asyncio

import pybotters

apis = {
    "bitflyer": ["BITFLYER_API_KEY", "BITFLYER_API_SECRET"],
}


async def main():
    async with pybotters.Client(
        apis=apis, base_url="https://api.bitflyer.com"
    ) as client:
        # REST API
        resp = await client.get(
            "/v1/getexecutions", params={"count": "1000", "before": "2452669860"}
        )
        data = await resp.json()
        print(data)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
