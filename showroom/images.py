"""Image helpers shared by the admin upload forms and the management commands.

Photos on this site are stored inside the database as data URLs so the project
stays portable between local SQLite and hosted PostgreSQL without needing
object storage. Every stored image is therefore re-encoded to WebP and capped
at roughly 150 KB, which keeps pages usable on a 4G connection.
"""

import base64
import hashlib
import io

MAX_IMAGE_BYTES = 150 * 1024
MAX_IMAGE_EDGE = 1600
THUMBNAIL_BYTES = 40 * 1024
THUMBNAIL_EDGE = 480
AVATAR_BYTES = 8 * 1024
AVATAR_EDGE = 128
HERO_BYTES = 80 * 1024
HERO_EDGE = 1400
QUALITY_STEPS = (82, 74, 66, 58, 50)
THUMBNAIL_QUALITY_STEPS = (78, 70, 62, 54, 46)
AVATAR_QUALITY_STEPS = (72, 64, 56, 48, 40)


def _encode_webp(image, steps=QUALITY_STEPS, cap=MAX_IMAGE_BYTES):
    """Re-encode a PIL image as WebP, shrinking quality until it fits the cap."""
    payload = None
    for quality in steps:
        buffer = io.BytesIO()
        image.save(buffer, 'WEBP', quality=quality, method=6)
        payload = buffer.getvalue()
        if len(payload) <= cap:
            break
    return payload


def _resample_filter():
    """Pillow 10 moved the resampling constants; support both layouts."""
    try:
        from PIL import Image
        return Image.Resampling.LANCZOS
    except AttributeError:
        from PIL import Image
        return Image.LANCZOS


def _prepare(image, max_edge=MAX_IMAGE_EDGE):
    if image.mode in ('RGBA', 'LA', 'P'):
        image = image.convert('RGBA')
    else:
        image = image.convert('RGB')
    if max(image.size) > max_edge:
        image.thumbnail((max_edge, max_edge), _resample_filter())
    return image


def bytes_to_data_url(raw, max_bytes=MAX_IMAGE_BYTES, max_edge=MAX_IMAGE_EDGE):
    """Compress raw image bytes into a WebP data URL."""
    try:
        from PIL import Image
    except ImportError:
        return ''
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except Exception:
        return ''
    payload = _encode_webp(_prepare(image, max_edge), QUALITY_STEPS, max_bytes)
    return 'data:image/webp;base64,' + base64.b64encode(payload).decode('ascii')


def thumbnail_data_url(raw, max_edge=THUMBNAIL_EDGE, max_bytes=THUMBNAIL_BYTES):
    """Build a small WebP data URL used for cards and gallery grids.

    A data URL is part of the HTML, so the browser cannot lazy-load it.
    Grids therefore use this small version and only open the full size image
    in the lightbox or on the product page.
    """
    try:
        from PIL import Image
    except ImportError:
        return ''
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except Exception:
        return ''
    payload = _encode_webp(
        _prepare(image, max_edge), THUMBNAIL_QUALITY_STEPS, max_bytes
    )
    return 'data:image/webp;base64,' + base64.b64encode(payload).decode('ascii')



def file_to_data_url(path):
    """Compress an image file on disk into a WebP data URL."""
    if not path or not path.exists():
        return ''
    return bytes_to_data_url(path.read_bytes())


def optimize_data_url(data_url):
    """Re-compress an existing data URL. Returns the input unchanged if it
    cannot be decoded, so a bad row is never destroyed."""
    if not data_url or not data_url.startswith('data:'):
        return data_url
    try:
        header, encoded = data_url.split(',', 1)
        raw = base64.b64decode(encoded)
    except Exception:
        return data_url
    if header.endswith('image/webp') and len(raw) <= MAX_IMAGE_BYTES:
        return data_url
    optimized = bytes_to_data_url(raw)
    return optimized or data_url


def avatar_data_url(raw, max_edge=AVATAR_EDGE, max_bytes=AVATAR_BYTES):
    """Build a tiny WebP data URL for round avatars such as testimonials."""
    try:
        from PIL import Image
    except ImportError:
        return ''
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except Exception:
        return ''
    payload = _encode_webp(
        _prepare(image, max_edge), AVATAR_QUALITY_STEPS, max_bytes
    )
    return 'data:image/webp;base64,' + base64.b64encode(payload).decode('ascii')


def thumbnail_from_data_url(data_url, max_edge=THUMBNAIL_EDGE, max_bytes=THUMBNAIL_BYTES):
    """Build a small data URL from an existing full-size data URL."""
    if not data_url or not data_url.startswith('data:'):
        return ''
    try:
        _, encoded = data_url.split(',', 1)
        raw = base64.b64decode(encoded)
    except Exception:
        return ''
    return thumbnail_data_url(raw, max_edge, max_bytes)


def avatar_from_data_url(data_url, max_edge=AVATAR_EDGE, max_bytes=AVATAR_BYTES):
    """Build an avatar-sized data URL from an existing full-size data URL."""
    if not data_url or not data_url.startswith('data:'):
        return ''
    try:
        _, encoded = data_url.split(',', 1)
        raw = base64.b64decode(encoded)
    except Exception:
        return ''
    return avatar_data_url(raw, max_edge, max_bytes)


_RESIZE_CACHE = {}
_RESIZE_CACHE_LIMIT = 64
_BYTES_CACHE = {}
_BYTES_CACHE_LIMIT = 128


def data_url_bytes(data_url):
    """Decode a ``data:`` URL to ``(raw_bytes, content_type)``, cached.

    Stored images never change, so the decode only has to happen once per
    process instead of on every request for the same picture.
    """
    if not data_url or not data_url.startswith('data:'):
        return b'', 'image/webp'
    key = hashlib.md5(data_url.encode('ascii', 'ignore')).hexdigest()
    cached = _BYTES_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        header, encoded = data_url.split(',', 1)
        raw = base64.b64decode(encoded)
    except Exception:
        return b'', 'image/webp'
    content_type = header[5:].split(';')[0] or 'image/webp'
    if len(_BYTES_CACHE) >= _BYTES_CACHE_LIMIT:
        _BYTES_CACHE.clear()
    _BYTES_CACHE[key] = (raw, content_type)
    return raw, content_type


def resize_data_url(data_url, max_edge=MAX_IMAGE_EDGE, max_bytes=MAX_IMAGE_BYTES):
    """Return a smaller WebP data URL for a stored image.

    Used by the image endpoint so a browser can ask for exactly the pixels it
    will paint, instead of downloading the full-size copy. Results are cached
    in memory because the source bytes never change once stored.
    """
    if not data_url or not data_url.startswith('data:'):
        return ''
    key = (hashlib.md5(data_url.encode('ascii', 'ignore')).hexdigest(), max_edge)
    cached = _RESIZE_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        from PIL import Image
    except ImportError:
        return data_url
    try:
        _, encoded = data_url.split(',', 1)
        raw = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(raw))
        image.load()
    except Exception:
        return data_url
    payload = _encode_webp(_prepare(image, max_edge), QUALITY_STEPS, max_bytes)
    if len(payload) >= len(raw):
        result = data_url
    else:
        result = 'data:image/webp;base64,' + base64.b64encode(payload).decode('ascii')
    if len(_RESIZE_CACHE) >= _RESIZE_CACHE_LIMIT:
        _RESIZE_CACHE.clear()
    _RESIZE_CACHE[key] = result
    return result
