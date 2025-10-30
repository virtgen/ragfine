import asyncio, inspect

async def _maybe_await(obj):
    return await obj if inspect.isawaitable(obj) else obj

async def _run_step_async(step_obj, state, variant, step_timeout=None):
    res = step_obj.run(state, variant)
    if inspect.isawaitable(res):
        res = await res
    if step_timeout is not None:
        return await asyncio.wait_for(asyncio.sleep(0, res), timeout=step_timeout)
    return res
