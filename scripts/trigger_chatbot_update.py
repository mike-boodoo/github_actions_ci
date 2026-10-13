"""Example chatbot backend call that triggers the chatbot-code-update workflow.

Usage:
    GITHUB_PAT=... CHATBOT_KEY=... python scripts/trigger_chatbot_update.py OWNER/REPO
"""

import base64
import hashlib
import hmac
import os
import sys

import requests


def dispatch(repo: str, payload: dict) -> int:
    resp = requests.post(
        f"https://api.github.com/repos/{repo}/dispatches",
        json={"event_type": "chatbot-code-update", "client_payload": payload},
        headers={
            "Authorization": f"Bearer {os.environ['GITHUB_PAT']}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )
    return resp.status_code  # 204 on success


if __name__ == "__main__":
    task_id, file_path = "t-1082", "utils/parser.py"
    code = "def parse_data(raw):\n    return raw.strip()\n"
    content = base64.b64encode(code.encode()).decode()
    # Sign the *encoded* content exactly as it appears in the payload.
    signature = hmac.new(
        os.environ["CHATBOT_KEY"].encode(),
        "\n".join([task_id, file_path, content]).encode(),
        hashlib.sha256,
    ).hexdigest()
    status = dispatch(
        sys.argv[1],
        {
            "task_id": task_id,
            "file_path": file_path,
            "file_content": content,
            "signature": signature,
            "content_encoding": "base64",
            "description": "Added whitespace parser helper.",
            "chatbot_id": "claude",
            "session_id": "sess_89jdf0239",
            "user_handle": "alice_dev",
            "interface_source": "internal-slack-bot",
        },
    )
    print(status)
