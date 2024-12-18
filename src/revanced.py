import httpx
from tools import cache_url
import time

class RevancedApiHandler:
    def __init__(self) -> None:
        self.base_url = "https://api.revanced.app/v4/"

    @cache_url
    def get_patches_release_via_api(self):
        url = self.base_url + "patches"
        response = httpx.get(url).json()
        return response

    @cache_url
    def get_patches_release_version_via_api(self):
        url = self.base_url + "patches/version"
        response = httpx.get(url).json()
        return response

class RevancedPatchesController:
    def __init__(self) -> None:
        pass

class RevancedPatcherController:
    def __init__(self) -> None:
        pass


if __name__ == "__main__":
    rah = RevancedApiHandler()
    print(rah.get_patches_release_version_via_api())