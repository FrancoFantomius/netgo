# Wikimedia Commons API: searching and inspecting media files.

Commons is the central media repository for every Wikimedia project, with tens of millions of free images, videos and audio files. This module wraps ``commons.wikimedia.org/w/api.php`` to find files by text and pull down their direct URLs, thumbnails and licensing metadata.

**Example:**
```python
>>> from netgo.wiki import search_images, image_url
>>> hits = search_images("sunflower", limit=3)
>>> bool(hits[0].name.startswith("File:"))
True
>>> url = image_url("File:Sunflower 2016.jpg")
>>> url.endswith(".jpg")
True
```

### `_plain(html: str) -> str`
Strip HTML out of Commons ``extmetadata`` text blocks.

### `search_images(query: str, limit: int = 10, client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[netgo.wiki.models.MediaFile]`
Search Commons for media files by free-text query.

Searches the ``File:`` namespace (namespace 6); each hit only carries the file name — use `file_info` for the URL and metadata of the ones you care about.

**Args:**
- `query`: The text to search for (tags, captions, categories...).
- `limit`: Maximum number of files to return.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of `MediaFile` with the file names populated.  

**Example:**
```python
>>> from netgo.wiki import search_images
>>> hits = search_images("cat", limit=2)
>>> hits[0].name or "File:..."
'File:...'
```

### `file_info(filename: str, thumb_width: int = 320, client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> netgo.wiki.models.MediaFile`
Return full metadata for a single Commons file.

Includes the direct download URL, a resized thumbnail (``thumburl``), dimensions, MIME type and licensing/author/description text from the file's ``extmetadata``.

**Args:**
- `filename`: The file title, e.g. ``"File:Earth.jpg"``.
- `thumb_width`: Pixel width of the generated thumbnail.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A populated `MediaFile`.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the file does not exist.

**Example:**
```python
>>> from netgo.wiki import file_info
>>> f = file_info("File:Earth.jpg")
>>> f.mime
'image/jpeg'
```

### `image_url(filename: str, client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> str`
Return the direct download URL of a Commons file.

Convenience wrapper over `file_info`.

**Args:**
- `filename`: The file title, e.g. ``"File:Earth.jpg"``.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- The absolute URL of the original file.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the file does not exist.

**Example:**
```python
>>> from netgo.wiki import image_url
>>> bool(image_url("File:Earth.jpg"))
True
```

### `random_file(limit: int = 1, client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[netgo.wiki.models.MediaFile]`
Return random files from the Commons repository.

Useful for wander-style exploration of the media library.

**Args:**
- `limit`: Number of random files to return.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of `MediaFile` with the file names populated.  

**Example:**
```python
>>> from netgo.wiki import random_file
>>> len(random_file(limit=2))
2
```