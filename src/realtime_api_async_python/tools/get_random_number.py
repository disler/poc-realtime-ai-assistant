import random
from ..utils.timeit_decorator import timeit_decorator


@timeit_decorator
async def get_random_number():
    return {"random_number": random.randint(1, 100)}
