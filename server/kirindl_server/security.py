from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit


class UnsafeURLError(ValueError):
    """Raised when a submitted URL is not safe for server-side fetching."""


def validate_public_http_url(raw_url: str) -> str:
    """Validate a public HTTP(S) URL and reject local/private network targets.

    This is a first-line SSRF guard, not a substitute for outbound network
    firewall rules. Extractors can follow redirects and request secondary hosts.
    """
    if not isinstance(raw_url, str) or not raw_url or len(raw_url) > 4096:
        raise UnsafeURLError("Enter a URL between 1 and 4096 characters.")

    try:
        parsed = urlsplit(raw_url.strip())
        port = parsed.port
    except ValueError as exc:
        raise UnsafeURLError("The URL format is invalid.") from exc

    if parsed.scheme.lower() not in {"http", "https"}:
        raise UnsafeURLError("Only http:// and https:// URLs are supported.")
    if not parsed.hostname:
        raise UnsafeURLError("The URL must include a host name.")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeURLError("URLs containing embedded credentials are not allowed.")
    if port not in {None, 80, 443}:
        raise UnsafeURLError("Only standard HTTP and HTTPS ports are allowed.")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith((".localhost", ".local", ".internal", ".test", ".invalid")):
        raise UnsafeURLError("Local and internal host names are not allowed.")

    try:
        literal_ip = ipaddress.ip_address(hostname)
        addresses = {literal_ip}
    except ValueError:
        try:
            results = socket.getaddrinfo(
                hostname,
                port or (443 if parsed.scheme.lower() == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise UnsafeURLError("The URL host could not be resolved.") from exc
        addresses = set()
        for result in results:
            try:
                addresses.add(ipaddress.ip_address(result[4][0].split("%", 1)[0]))
            except ValueError:
                continue

    if not addresses:
        raise UnsafeURLError("The URL host did not resolve to a valid IP address.")
    if any(not address.is_global for address in addresses):
        raise UnsafeURLError("URLs resolving to private, local or reserved IP addresses are not allowed.")

    return urlunsplit((parsed.scheme.lower(), parsed.netloc, parsed.path or "/", parsed.query, ""))
