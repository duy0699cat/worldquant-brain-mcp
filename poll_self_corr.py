import asyncio
from datetime import datetime
from worldquant_mcp.config import WorldQuantConfig
from worldquant_mcp.client import WorldQuantClient

async def main():
    settings = WorldQuantConfig.from_env()
    c = WorldQuantClient(settings)
    if asyncio.iscoroutinefunction(c.authenticate): await c.authenticate()
    else: c.authenticate()
    
    print('Poll Timestamp: ' + datetime.now().isoformat())
    for aid in ['[REDACTED]', '[REDACTED]', '[REDACTED]']:
        try:
            res = c._get_json('/alphas/' + aid)
            if asyncio.iscoroutine(res): res = await res
            checks = res.get('is', {}).get('checks', [])
            sc = next((x for x in checks if x['name'] == 'SELF_CORRELATION'), {})
            print(aid + ': SELF_CORRELATION = ' + str(sc.get('result', 'UNKNOWN')))
        except Exception as e:
            print(aid + ': Error - ' + str(e))
    if asyncio.iscoroutinefunction(c.close): await c.close()
    else: c.close()

asyncio.run(main())
