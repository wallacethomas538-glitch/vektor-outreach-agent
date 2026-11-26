"""Meta Model API brain for the Vektor Outreach Agent.

Standard library only. The API key comes from the META_MODEL_API_KEY
environment variable and is never hardcoded or logged. If the key is
missing, no call is made.
"""

import json
import os
import urllib.error
import urllib.request

API_URL = "https://api.meta.ai/v1/chat/completions"
DEFAULT_MODEL = "muse-spark"


class MissingKeyError(RuntimeError):
    """Raised when META_MODEL_API_KEY is not set. No API call is made."""


class BrainError(RuntimeError):
    """Raised when the Meta Model API call fails."""


def get_api_key():
    key = os.environ.get("META_MODEL_API_KEY", "").strip()
    if not key:
        raise MissingKeyError(
            "META_MODEL_API_KEY is not set. Set it in the environment where "
            "this agent runs, then try again. No API call was made."
        )
    return key


def get_model():
    return os.environ.get("META_MODEL", "").strip() or DEFAULT_MODEL


def chat(messages, model=None, timeout=60):
    """Send a chat completion request. Returns the assistant's text."""
    key = get_api_key()  # raises before any network activity if missing
    payload = json.dumps(
        {"model": model or get_model(), "messages": messages}
    ).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        raise BrainError(
            "Meta Model API returned HTTP %s. Check the key, the model name "
            "(META_MODEL), and that api.meta.ai is reachable from this machine."
            % error.code
        ) from None
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise BrainError(
            "Could not reach api.meta.ai from this machine (%s). The agent "
            "must run somewhere that can reach the Meta Model API."
            % (getattr(error, "reason", error),)
        ) from None
    try:
        data = json.loads(body)
        return data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        raise BrainError("Meta Model API returned an unexpected response shape.") from None
