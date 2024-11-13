import httpx
from urllib.parse import urlparse, unquote
import re
import mimetypes
from datetime import datetime
import hashlib
from typing import Optional

from tqdm import tqdm

def parse_content_disposition(header: str):
    """
    Parse Content-Disposition header value into components.
    
    Args:
        header (str): Content-Disposition header value
    
    Returns:
        Dict[str, str]: Dictionary of parameters
    """
    params = {}
    
    # Split the header into components
    parts = header.split(';')
    
    for part in parts[1:]:  # Skip the first part (e.g., "attachment")
        if '=' not in part:
            continue
            
        name, value = part.split('=', 1)
        name = name.strip().lower()
        value = value.strip()
        
        # Remove quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        
        params[name] = value
        
    return params

def extract_filename_from_url(
    url: str,
    default_extension: Optional[str] = None,
    check_headers: bool = True,
    timeout: int = 5
):
    """
    Extract a meaningful filename from a URL, checking both headers and URL structure.
    
    Args:
        url (str): The URL to process
        default_extension (str, optional): Default file extension if none can be determined
        check_headers (bool): Whether to make a HEAD request to check headers
        timeout (int): Timeout in seconds for the HEAD request
    
    Returns:
        str: Generated filename
    """
    # Initialize mimetypes
    mimetypes.init()
    
    # Clean and parse URL
    url = url.strip()
    parsed = urlparse(unquote(url))
    
    filename = None
    content_type = None
    
    # Try to get filename from headers
    if check_headers:
        try:
            with httpx.Client() as client:
                response = client.head(url, timeout=timeout, follow_redirects=True)
                response.raise_for_status()
                
                # Check Content-Disposition header
                content_disposition = response.headers.get('content-disposition')
                if content_disposition:
                    params = parse_content_disposition(content_disposition)
                    
                    # Try filename* (RFC 5987) first
                    if 'filename*' in params:
                        # Parse RFC 5987 encoded filename
                        value = params['filename*']
                        if "'" in value:
                            try:
                                # Format: encoding'language'value
                                encoding, _, encoded_filename = value.split("'", 2)
                                filename = unquote(encoded_filename)
                            except Exception:
                                pass
                    
                    # Fall back to regular filename
                    if not filename and 'filename' in params:
                        filename = params['filename']
                
                content_type = response.headers.get('content-type', '').split(';')[0].lower()
        except Exception:
            pass
    
    # If no filename from headers, try URL path
    if not filename:
        path = parsed.path.rstrip('/')
        if path and path != '/':
            path_parts = [p for p in path.split('/') if p and not p.startswith('?')]
            if path_parts:
                filename = path_parts[-1]
    
    # If still no filename, use domain or generate one
    if not filename or filename == '/':
        base = parsed.netloc.split(':')[0] or 'download'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"{base}_{timestamp}_{url_hash}"
    
    # Clean the filename (before extension processing)
    base_name = re.sub(r'[^\w\-_.]', '_', filename)
    base_name = re.sub(r'_+', '_', base_name.rsplit('.', 1)[0])
    
    # Determine extension
    extension = None
    
    # Try to get extension from original filename
    if '.' in filename:
        orig_ext = filename.rsplit('.', 1)[-1].lower()
        if len(orig_ext) <= 4:
            extension = orig_ext
    
    # If no extension, try content type
    if not extension and content_type:
        extension = mimetypes.guess_extension(content_type, strict=False)
        if extension:
            extension = extension[1:]  # Remove leading dot
    
    # If still no extension, try URL query parameters
    if not extension:
        query_params = parsed.query
        if 'type=' in query_params:
            mime_type = re.search(r'type=([^&]+)', query_params)
            if mime_type:
                mime = mime_type.group(1).lower()
                extension = mimetypes.guess_extension(mime, strict=False)
                if extension:
                    extension = extension[1:]
    
    # Use default extension as last resort
    if not extension and default_extension:
        extension = default_extension
    
    # Combine filename and extension
    if extension:
        return f"{base_name}.{extension}"
    
    return base_name

def download_file(url:str, filename: str = "auto"):
    filename = extract_filename_from_url(url=url) if filename == "auto" else filename
    
    with open(filename, "wb") as download_file:
        with httpx.stream("GET", url) as response:
            total = int(response.headers["Content-Length"])

            with tqdm(total=total, unit_scale=True, unit_divisor=1024, unit="B") as progress:
                num_bytes_downloaded = response.num_bytes_downloaded
                for chunk in response.iter_bytes():
                    download_file.write(chunk)
                    progress.update(response.num_bytes_downloaded - num_bytes_downloaded)
                    num_bytes_downloaded = response.num_bytes_downloaded
   

if __name__ == "__main__":
    download_file(url="https://images.unsplash.com/photo-1601850494422-3cf14624b0b3?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb")
