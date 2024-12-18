import httpx
from diskcache import Cache

cache = Cache('./cache_directory')

def cache_url(func):
    def wrapper(self, *args, **kwargs):
        url = self.base_url + "patches"  
        key = f"cache__{url}"  
        
        result = cache.get(key)
        if result is not None:
            print(f"Using cached result for {url}")
            return result
        
        print(f"Making actual API call to {url}")
        result = func(self, *args, **kwargs)
        cache.set(key, result, expire=300)  # Cache for 5 minutes
        return result
    return wrapper

