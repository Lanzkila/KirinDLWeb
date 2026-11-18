from __future__ import annotations

import json
import uuid
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class TurnstileVerificationError(ValueError):
    """The submitted challenge token was not accepted."""


class TurnstileUnavailableError(RuntimeError):
    """Cloudflare Siteverify could not be reached or returned invalid data."""


def verify_turnstile_token(
    token: str,
    secret: str,
    allowed_hostnames: set[str],
    expected_action: str = "download",
    timeout_seconds: float = 8.0,
) -> None:
    """Validate a single-use Turnstile token against Cloudflare Siteverify."""
    if not isinstance(token, str) or not token or len(token) > 2048:
        raise TurnstileVerificationError("Complete the security check before downloading.")
    if not secret:
        raise TurnstileUnavailableError("The server-side security check is not configured.")
    if not allowed_hostnames:
        raise TurnstileUnavailableError("No allowed Turnstile hostnames are configured.")

    payload = urlencode({
        "secret": secret,
        "response": token,
        "idempotency_key": str(uuid.uuid4()),
    }).encode("ascii")
    request = Request(
        SITEVERIFY_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, OSError) as exc:
        raise TurnstileUnavailableError("The security verification service is temporarily unavailable.") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TurnstileUnavailableError("The security verification service returned an invalid response.") from exc

    if not isinstance(result, dict):
        raise TurnstileUnavailableError("The security verification service returned an invalid response.")
    if result.get("success") is not True:
        raise TurnstileVerificationError("The security check expired or was not accepted. Please try again.")

    hostname = str(result.get("hostname") or "").strip().lower().rstrip(".")
    action = str(result.get("action") or "").strip()
    normalized_hosts = {item.strip().lower().rstrip(".") for item in allowed_hostnames if item.strip()}
    if hostname not in normalized_hosts:
        raise TurnstileVerificationError("The security check was issued for an unrecognised website.")
    if action != expected_action:
        raise TurnstileVerificationError("The security check does not match this download action.")
