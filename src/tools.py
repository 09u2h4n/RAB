import httpx
import mimetypes
from pathlib import Path
import tempfile

from typing import Union

def guess_extension(url: str) -> str:
    return mimetypes.guess_extension(mimetypes.guess_type(url)[0])

def find_file_name(url: str, response_headers) -> str:
    

def download_file(url: str, download_path: Union[Path, str], file_name: str = None):
    file_extension = guess_extension(url)
    with httpx.stream("GET", url) as response:
        file_name = find_file_name(url, response.headers) if file_name else tempfile.mkstemp

if __name__ == "__main__":
    download_file(url="https://images.unsplash.com/photo-1601850494422-3cf14624b0b3?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb")
