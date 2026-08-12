# netgo.page - fetch web pages and read their main content.

Given a URL, `fetch` downloads the page and reduces it to the actual article, filtering out the site template that surrounds it: navigation, headers, footers, sidebars, ad banners, comment widgets and cookie banners. The result is a `Page` carrying the extracted title and domain, the cleaned plain-text body (also split into :attr:`Page.paragraphs`) and the extracted content HTML.

Every failure is raised as a ``PageError`` subclass, so a ``try/except PageError`` covers fetching and parsing alike.

**Example:**
```python
>>> from netgo import page
>>> p = page.fetch("https://en.wikipedia.org/wiki/Bread")
>>> p.title
'Bread'
>>> p.text.startswith("Bread is")
True
```