import time
from .loger import comfyui_loggerr

class Testing:
    @staticmethod
    def timing_use(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            comfyui_loggerr.debug(f"Function '{func.__name__}' executed in {execution_time:.4f} seconds")
            return result
        return wrapper