"""Validate a chatbot repository_dispatch payload and write the file.

Reads all input from environment variables (set by the workflow) and emits
step outputs (branch, author_name, author_email) via $GITHUB_OUTPUT.
"""

import base64
import hashlib
import hmac
import json
import os
import re
import sys
from pathlib import Path

BLOCKED_PREFIXES = (".github/", ".git/")
TASK_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
HANDLE_RE = re.compile(r"[^A-Za-z0-9._-]")


def fail(msg: str) -> None:
    print(f"::error::{msg}")
    sys.exit(1)


def signing_message(task_id: str, file_path: str, content: str) -> bytes:
    return "\n".join([task_id, file_path, content]).encode()


def verify_chatbot(chatbot_id: str, file_path: str, task_id: str, content: str) -> None:
    """Only accept allowlisted chatbots that sign the payload with their key."""
    allowlist = json.loads(Path(".github/chatbot-allowlist.json").read_text())
    entry = allowlist.get("chatbots", {}).get(chatbot_id)
    if entry is None:
        fail(f"chatbot_id '{chatbot_id}' is not in the allowlist")

    check_attributes(entry, allowlist)

    prefixes = entry.get("allowed_path_prefixes", [])
    if prefixes and not file_path.startswith(tuple(prefixes)):
        fail(f"chatbot '{chatbot_id}' may not write to {file_path}")

    keys = json.loads(os.environ.get("CHATBOT_KEYS") or "{}")
    key = keys.get(chatbot_id)
    if not key:
        fail(f"no signing key configured for chatbot '{chatbot_id}'")
    expected = hmac.new(
        key.encode(), signing_message(task_id, file_path, content), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, os.environ.get("SIGNATURE", "")):
        fail("invalid payload signature")


def check_attributes(entry: dict, allowlist: dict) -> None:
    """Reject payloads missing a required attribute or carrying a forbidden one."""
    payload = json.loads(os.environ.get("PAYLOAD_JSON") or "{}")
    required = entry.get(
        "required_attributes", allowlist.get("required_attributes", [])
    )
    forbidden = entry.get(
        "forbidden_attributes", allowlist.get("forbidden_attributes", [])
    )
    missing = [a for a in required if payload.get(a) in (None, "")]
    if missing:
        fail(f"payload is missing required attribute(s): {', '.join(missing)}")
    present = [a for a in forbidden if a in payload]
    if present:
        fail(f"payload contains forbidden attribute(s): {', '.join(present)}")


def main() -> None:
    task_id = os.environ.get("TASK_ID", "")
    file_path = os.environ.get("FILE_PATH", "")
    content = os.environ.get("FILE_CONTENT", "")
    encoding = os.environ.get("CONTENT_ENCODING", "") or "raw"

    if not TASK_ID_RE.fullmatch(task_id):
        fail("task_id must match [A-Za-z0-9._-]{1,64}")
    if not file_path:
        fail("file_path is required")

    root = Path.cwd().resolve()
    target = (root / file_path).resolve()
    if root not in target.parents:
        fail("file_path must stay inside the repository")
    rel = target.relative_to(root).as_posix()
    verify_chatbot(os.environ.get("CHATBOT_ID", ""), rel, task_id, content)
    if rel.startswith(BLOCKED_PREFIXES):
        fail("chatbot changes to .github/ and .git/ are not allowed")

    if encoding == "base64":
        try:
            data = base64.b64decode(content, validate=True)
        except ValueError:
            fail("file_content is not valid base64")
    elif encoding == "raw":
        data = content.encode()
    else:
        fail("content_encoding must be 'raw' or 'base64'")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)

    bot = HANDLE_RE.sub("-", os.environ["CHATBOT_ID"])
    user = HANDLE_RE.sub("-", os.environ.get("USER_HANDLE") or "unknown")
    with open(os.environ["GITHUB_OUTPUT"], "a") as out:
        out.write(f"branch=chatbot/feature-{task_id}\n")
        out.write(f"author_name={bot} (via {user})\n")
        out.write(f"author_email={bot}@users.noreply.github.com\n")


if __name__ == "__main__":
    main()
