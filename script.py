import asyncio
import datetime
from worldquant_mcp.config import WorldQuantConfig
from worldquant_mcp.client import WorldQuantClient
async def main():
    settings = WorldQuantConfig.from_env()
    c = WorldQuantClient(settings)
    if asyncio.iscoroutinefunction(c.authenticate): await c.authenticate()
    else: c.authenticate()
    print('Poll Timestamp:', datetime.datetime.now().isoformat())
    for aid in ['QP2NPG6X', 'RRNX8Zz0', 'zq5aX5PK']:
        res = c._get_json('/alphas/' + aid)
        if asyncio.iscoroutine(res): res = await res
        checks = res.get('is', {}).get('checks', [])
        sc = next((x for x in checks if x['name'] == 'SELF_CORRELATION'), {})
        print(aid, 'SELF_CORRELATION =', sc.get('result', 'UNKNOWN'))
    if asyncio.iscoroutinefunction(c.close): await c.close()
    else: c.close()
asyncio.run(main())
