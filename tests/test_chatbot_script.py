import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = (
    Path(__file__).parent.parent / ".github" / "scripts" / "apply_chatbot_change.py"
)
ALLOWLIST = Path(__file__).parent.parent / ".github" / "chatbot-allowlist.json"
KEY = "s3cret"


def sign(task_id: str, path: str, content: str, key: str = KEY) -> str:
    msg = "\n".join([task_id, path, content]).encode()
    return hmac.new(key.encode(), msg, hashlib.sha256).hexdigest()


def run(tmp_path, **overrides):
    (tmp_path / ".github").mkdir(exist_ok=True)
    allowlist = overrides.pop("_ALLOWLIST", None) or ALLOWLIST.read_text()
    (tmp_path / ".github" / "chatbot-allowlist.json").write_text(allowlist)
    content = base64.b64encode(b"print(1)\n").decode()
    env = {
        **os.environ,
        "TASK_ID": "t-1",
        "FILE_PATH": "utils/a.py",
        "FILE_CONTENT": content,
        "CONTENT_ENCODING": "base64",
        "CHATBOT_ID": "claude",
        "USER_HANDLE": "alice",
        "CHATBOT_KEYS": json.dumps({"claude": KEY, "internal-slack-bot": KEY}),
        "GITHUB_OUTPUT": str(tmp_path / "out"),
    }
    env["PAYLOAD_JSON"] = json.dumps(
        {
            "task_id": "t-1",
            "description": "d",
            "session_id": "s",
            "user_handle": "alice",
        }
    )
    env["SIGNATURE"] = sign(env["TASK_ID"], env["FILE_PATH"], env["FILE_CONTENT"])
    env.update(overrides)
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )


def test_allowed_chatbot_writes_file(tmp_path):
    r = run(tmp_path)
    assert r.returncode == 0, r.stdout
    assert (tmp_path / "utils/a.py").read_text() == "print(1)\n"
    assert "branch=chatbot/feature-t-1" in (tmp_path / "out").read_text()


def test_unknown_chatbot_rejected(tmp_path):
    r = run(tmp_path, CHATBOT_ID="rogue-bot")
    assert r.returncode == 1 and "not in the allowlist" in r.stdout


def test_bad_signature_rejected(tmp_path):
    r = run(tmp_path, SIGNATURE="deadbeef")
    assert r.returncode == 1 and "invalid payload signature" in r.stdout


def test_signature_from_other_chatbots_key_rejected(tmp_path):
    sig = sign("t-1", "utils/a.py", base64.b64encode(b"print(1)\n").decode(), "wrong")
    r = run(tmp_path, SIGNATURE=sig)
    assert r.returncode == 1 and "invalid payload signature" in r.stdout


def test_path_prefix_enforced_per_chatbot(tmp_path):
    r = run(tmp_path, CHATBOT_ID="internal-slack-bot")
    assert r.returncode == 1 and "may not write" in r.stdout


def test_workflow_files_blocked(tmp_path):
    r = run(tmp_path, FILE_PATH=".github/workflows/x.yml")
    assert r.returncode == 1


def test_path_traversal_blocked(tmp_path):
    assert run(tmp_path, FILE_PATH="../x").returncode == 1


def test_missing_required_attribute_rejected(tmp_path):
    payload = json.dumps({"task_id": "t-1", "description": "d", "user_handle": "a"})
    r = run(tmp_path, PAYLOAD_JSON=payload)
    assert r.returncode == 1 and "session_id" in r.stdout


def test_empty_required_attribute_rejected(tmp_path):
    payload = json.dumps(
        {"task_id": "t-1", "description": "", "session_id": "s", "user_handle": "a"}
    )
    r = run(tmp_path, PAYLOAD_JSON=payload)
    assert r.returncode == 1 and "description" in r.stdout


def test_forbidden_attribute_rejected(tmp_path):
    cfg = json.loads(ALLOWLIST.read_text())
    cfg["forbidden_attributes"] = ["skip_review"]
    # run() overwrites the allowlist, so patch after via env-independent copy
    payload = json.dumps(
        {
            "task_id": "t-1",
            "description": "d",
            "session_id": "s",
            "user_handle": "a",
            "skip_review": True,
        }
    )
    r = run(tmp_path, PAYLOAD_JSON=payload, _ALLOWLIST=json.dumps(cfg))
    assert r.returncode == 1 and "forbidden" in r.stdout
