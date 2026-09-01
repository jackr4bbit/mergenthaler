from urllib.parse import urlparse, urlsplit

def validUrl(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def removeScheme(url):
    parsed = urlsplit(url)

    if parsed.scheme:
        return url.split("://", 1)[1]

    if url.startswith("//"):
        return url[2:]

    return url