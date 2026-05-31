"""API channel adapter.

Each channel has exactly 2 methods:
- read(url, ...) -> dict (input via HTTP)
- export(url, data) -> dict (output via HTTP POST/PUT)
"""

from __future__ import annotations

import json
import time
from typing import Any, Generator
from urllib.parse import urlparse

from ..exceptions import ChannelReadError


class APIChannel:
    """Fetches data from REST APIs and exports normalized JSON to endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = 30,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self._session = None
        self._auth_token = None

    @property
    def session(self):
        """Lazy-initialized requests session."""
        if self._session is None:
            import requests
            self._session = requests.Session()
            self._session.timeout = self.timeout
        return self._session

    def read(
        self,
        url: str,
        method: str = "GET",
        headers: dict | None = None,
        params: dict | None = None,
        json_body: dict | None = None,
        auth: tuple | None = None,
    ) -> dict | list:
        """Make HTTP request and return JSON.

        Args:
            url: URL to fetch
            method: HTTP method (GET, POST, etc.)
            headers: Additional headers
            params: Query parameters
            json_body: JSON body for POST/PUT
            auth: Basic auth tuple (user, pass)

        Returns:
            Parsed JSON response (dict or list)
        """
        full_url = url if url.startswith("http") else f"{self.base_url}/{url}"

        request_headers = {"Accept": "application/json"}
        if headers:
            request_headers.update(headers)
        if self._auth_token:
            request_headers["Authorization"] = f"Bearer {self._auth_token}"

        last_error = None
        for attempt in range(self.retry_count):
            try:
                response = self.session.request(
                    method=method,
                    url=full_url,
                    headers=request_headers,
                    params=params,
                    json=json_body,
                    auth=auth,
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                last_error = e
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))

        raise ChannelReadError(f"Failed to fetch {full_url} after {self.retry_count} attempts: {last_error}")

    def export(self, url: str, data: dict, method: str = "POST", headers: dict | None = None) -> dict:
        """Export normalized JSON to an endpoint.

        Args:
            url: URL to POST to
            data: Normalized JSON dict (metadata + records)
            method: HTTP method (POST, PUT)
            headers: Additional headers

        Returns:
            Response from the endpoint
        """
        full_url = url if url.startswith("http") else f"{self.base_url}/{url}"

        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        if self._auth_token:
            request_headers["Authorization"] = f"Bearer {self._auth_token}"

        last_error = None
        for attempt in range(self.retry_count):
            try:
                response = self.session.request(
                    method=method,
                    url=full_url,
                    headers=request_headers,
                    json=data,
                )
                response.raise_for_status()
                return response.json() if response.content else {"status": "ok"}
            except Exception as e:
                last_error = e
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))

        raise ChannelReadError(f"Failed to export to {full_url} after {self.retry_count} attempts: {last_error}")

    def paginate(
        self,
        url: str,
        page_param: str = "page",
        page_size_param: str = "page_size",
        max_pages: int = 100,
        page_size: int = 100,
    ) -> Generator[dict, None, None]:
        """Handle paginated API responses."""
        page = 1
        while page <= max_pages:
            params = {page_param: page, page_size_param: page_size}
            data = self.read(url, params=params)

            if isinstance(data, list):
                if not data:
                    break
                yield from data
                if len(data) < page_size:
                    break
            elif isinstance(data, dict):
                items_key = None
                for key in ["data", "items", "results", "records"]:
                    if key in data and isinstance(data[key], list):
                        items_key = key
                        break

                if items_key is None:
                    break

                items = data[items_key]
                if not items:
                    break
                yield from items
                if len(items) < page_size:
                    break

                if "has_more" in data and not data["has_more"]:
                    break
            else:
                break

            page += 1

    def authenticate(
        self,
        credentials: dict,
        auth_type: str = "bearer",
        token_url: str | None = None,
    ) -> str:
        """Get auth token for protected endpoints."""
        if auth_type == "bearer":
            self._auth_token = credentials.get("token")
            return self._auth_token
        elif auth_type == "oauth2":
            token_url = token_url or f"{self.base_url}/oauth/token"
            response = self.session.post(
                token_url,
                data=credentials,
            )
            response.raise_for_status()
            token_data = response.json()
            self._auth_token = token_data.get("access_token")
            return self._auth_token
        elif auth_type == "api_key":
            self._auth_token = credentials.get("api_key")
            return self._auth_token
        else:
            raise ValueError(f"Unknown auth type: {auth_type}")

    def graphql(self, url: str, query: str, variables: dict | None = None) -> dict:
        """Execute GraphQL query."""
        return self.read(
            url,
            method="POST",
            json_body={"query": query, "variables": variables or {}},
        )
