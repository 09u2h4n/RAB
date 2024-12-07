import httpx
import mimetypes
from pathlib import Path
import tempfile
from urllib.parse import urlparse
import uuid

from typing import Union, Optional

class Downloader:

    def find_extension(self, url: Optional[str], response_headers: Optional[dict]) -> str:
        # find from headers
        if response_headers:
            ext = response_headers["Content-Type"]
            ext = mimetypes.guess_extension(ext)
            return ext if ext else ""
        # find by guessing type and extension
        elif url:
            ext = mimetypes.guess_extension(mimetypes.guess_type(url))
            return ext if ext else ""

    def find_file_name(self, url: Optional[str], response_headers: Optional[dict]):
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
                ext = self.find_extension(url, response_headers)
                return file_name+ext if "" == ext else file_name+"."+ext
            else:
            # generate random file_name with uuid
                file_name = str(uuid.uuid4())
                ext = self.find_extension(url, response_headers)
                return file_name+ext if "." in ext else file_name+"."+ext

    def stream_data(self, url: str, file_name: str = None):
        with httpx.stream("GET", url) as response:
            file_name = self.find_file_name(url, response.headers)
            total = int(response.headers["Content-Length"])
            yield {"total": total, "file_name": file_name}
            for chunk in response.iter_bytes():
                yield {"chunk": chunk, "num_bytes_downloaded": response.num_bytes_downloaded}

    def download_file_with_tqdm(self, url: str, file_name: str = None, path: Union[Path, str] = "."):
        from tqdm import tqdm

        path = path if isinstance(path, Path) else Path(path)
        downloader = self.stream_data(url)
        metadata = next(downloader)
        total = metadata["total"]
        file_name = file_name if file_name else metadata["file_name"]

        with tqdm(total=total, unit_scale=True, unit_divisor=1024, unit="B") as progress:
            num_bytes_downloaded = 0
            with open(path / file_name, "wb") as file:
                for data in downloader:
                    file.write(data["chunk"])
                    progress.update(data["num_bytes_downloaded"] - num_bytes_downloaded)
                    num_bytes_downloaded = data["num_bytes_downloaded"]

    def download_file_with_rich(self, url: str, file_name: str = None, path: Union[Path, str] = "."):
        import rich.progress

        path = path if isinstance(path, Path) else Path(path)
        downloader = self.stream_data(url)
        metadata = next(downloader)
        total = metadata["total"]
        file_name = file_name if file_name else metadata["file_name"]

        with rich.progress.Progress() as progress:
            download_task = progress.add_task("Download", total=total)
            with open(path / file_name, "wb") as file:
                for data in downloader:
                    file.write(data["chunk"])
                    progress.update(download_task, completed = data["num_bytes_downloaded"])

if __name__ == "__main__":
    url1 = "https://images.unsplash.com/photo-1601850494422-3cf14624b0b3?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb"
    # url2 = "https://speed.hetzner.de/100MB.bin"
    Downloader().download_file_with_rich(url1)
    Downloader().download_file_with_tqdm(url1)
