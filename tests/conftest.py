"""Shared offline fixtures for the netgo.wiki tests.

The wrappers are exercised against canned JSON payloads instead of the
live Wikimedia API, so the suite needs no network. :class:`FakeSession`
pretends to be a :class:`requests.Session`, records the request it
received and returns the configured JSON payload (or fails with the
configured error), which every test injects through a
:class:`~netgo.wiki.WikiClient`.
"""

import requests


class FakeResponse:
    def __init__(self, payload=None, status=200, non_json=False):
        self._payload = payload
        self.status_code = status
        self._non_json = non_json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        if self._non_json:
            raise ValueError("not json")
        if callable(self._payload):
            return self._payload()
        return self._payload


class FakeSession:
    def __init__(self, payload=None, status=200, non_json=False, http_error=None):
        self.response = FakeResponse(payload, status, non_json)
        self.http_error = http_error
        self.last_url = None
        self.last_params = None

    def get(self, url, params=None, headers=None, timeout=None):
        self.last_url = url
        self.last_params = params
        if self.http_error is not None:
            raise self.http_error
        resp = self.response
        resp.raise_for_status()
        return resp