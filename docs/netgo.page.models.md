# Data model returned by :func:`netgo.page.fetch`.

`Page` carries the reduced view of a web page: only the main content is kept, with the site template (navigation, headers, footers, sidebars, banners) filtered out.

**Example:**
```python
>>> from netgo import page
>>> p = page.fetch("https://en.wikipedia.org/wiki/Bread")
>>> p.title
'Bread'
>>> p.paragraphs[0].startswith("Bread is")
True
```

### class `Page`
```python
Page(url: 'str', title: 'str' = '', site: 'str' = '', text: 'str' = '', paragraphs: 'list[str]' = <factory>, html: 'str' = '', raw: 'str' = '') -> None
```
The readable content of a fetched web page.

``title`` is the page title and ``site`` the bare domain name; ``text`` and ``paragraphs`` hold the extracted main content (one block per heading/paragraph), ``html`` keeps the cleaned content subtree so callers can render it or feed it to other parsers, and ``raw`` keeps the untouched HTML exactly as the server sent it.

**Example:**
```python
>>> from netgo import page
>>> p = page.fetch("https://www.bbc.co.uk/news/technology-1000001")
>>> p.site
'bbc.co.uk'
>>> bool(p.text)
True
```
**Fields:**
- `url`
- `title`
- `site`
- `text`
- `paragraphs`
- `html`
- `raw`