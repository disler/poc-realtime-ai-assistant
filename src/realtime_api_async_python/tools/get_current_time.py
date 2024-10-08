from datetime import datetime
from ..utils.timeit_decorator import timeit_decorator


@timeit_decorator
async def get_current_time():
    return {"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
