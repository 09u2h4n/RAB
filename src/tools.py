import httpx
import mimetypes
from pathlib import Path
import tempfile
from urllib.parse import urlparse
import uuid
from tqdm import tqdm

from typing import Union, Optional

def find_extension(url: Optional[str], response_headers: Optional[dict]) -> str:
    # find from headers
    if response_headers:
        ext = response_headers["Content-Type"]
        ext = mimetypes.guess_extension(ext)
        return ext if ext else ""
    # find by guessing type and extension
    elif url:
        ext = mimetypes.guess_extension(mimetypes.guess_type(url))
        return ext if ext else ""

def find_file_name(url: Optional[str], response_headers: Optional[dict]):
    # search in the response headers
    if "Content-Disposition" in response_headers.keys():
        suggested_file_name = response_headers["Content-Disposition"].split("filename=")[1]
        suggested_file_name = suggested_file_name.replace('"', "")
        return suggested_file_name
    # finding file name from url parsing via mimetypes
    elif response_headers and url:
        url_parsed = urlparse(url)
        if "filename" in str(url_parsed.path):
            file_name = url_parsed.path.split("/")[-1]
            ext = find_extension(url, response_headers)
            return file_name+ext if "" == ext else file_name+"."+ext
        else:
        # generate random file_name with uuid
            file_name = str(uuid.uuid4())
            ext = find_extension(url, response_headers)
            return file_name+ext if "." in ext else file_name+"."+ext

def download_file(url: str, download_path: Optional[Union[Path, str]] = ".", file_name: str = None):
    with httpx.stream("GET", url) as response:
        file_name = find_file_name(url, response.headers)
        total = int(response.headers["Content-Length"])
        with open(download_path + "/" + file_name, "wb") as file:
            with tqdm(total=total, unit_scale=True, unit_divisor=1024, unit="B") as progress:
                num_bytes_downloaded = response.num_bytes_downloaded
                for chunk in response.iter_bytes():
                    file.write(chunk)
                    progress.update(response.num_bytes_downloaded - num_bytes_downloaded)
                    num_bytes_downloaded = response.num_bytes_downloaded


if __name__ == "__main__":
    download_file(url="https://images.unsplash.com/photo-1601850494422-3cf14624b0b3?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb")
