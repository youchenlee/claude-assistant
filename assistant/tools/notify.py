#!/usr/bin/env python3
"""
Telegram notification tool for the assistant.

Sends messages to configured Telegram chats. Designed for use by scheduled
tasks, automation scripts, or any process that needs to push notifications.

Usage:
  python3 notify.py "message text"
  python3 notify.py -f message.txt          # read from file
  echo "content" | python3 notify.py --stdin # read from stdin

Environment variables (take precedence):
  ASSISTANT_TELEGRAM_TOKEN   - Bot token
  ASSISTANT_ALLOWED_CHATS    - Recipient chat_id(s), comma-separated

Fallback: reads telegram_token / telegram_chat_id from config.json
in the same directory as this script.

Features:
  - Deduplication: identical messages within a 10-minute window are skipped
  - Auto-chunking: messages longer than 4000 characters are split automatically
  - Multiple recipients: sends to all configured chat IDs

Exit codes:
  0 - Success (or duplicate skipped)
  1 - Error (missing config, empty message, send failure)
"""

import hashlib
import json
import os
import sys
import time
import urllib.request

DEDUP_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "logs", ".notify-dedup.json"
)
DEDUP_WINDOW = 600  # 10 minutes — skip identical content within this window


def _check_dedup(text):
    """Return True if the same content was already sent within DEDUP_WINDOW."""
    h = hashlib.md5(text.encode()).hexdigest()
    now = time.time()
    try:
        with open(DEDUP_FILE) as f:
            records = json.load(f)
    except Exception:
        records = {}
    # Purge expired entries
    records = {k: v for k, v in records.items() if now - v < DEDUP_WINDOW}
    if h in records:
        return True
    records[h] = now
    try:
        os.makedirs(os.path.dirname(DEDUP_FILE), exist_ok=True)
        with open(DEDUP_FILE, "w") as f:
            json.dump(records, f)
    except Exception:
        pass
    return False


def _load_config():
    """Load config.json from the same directory as this script."""
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "config.json"
    )
    try:
        with open(config_path) as f:
            return json.load(f)
    except Exception:
        return {}


_config = _load_config()

BOT_TOKEN = (
    os.environ.get("ASSISTANT_TELEGRAM_TOKEN") or _config.get("telegram_token", "")
)
_chat_env = os.environ.get("ASSISTANT_ALLOWED_CHATS", "")
if _chat_env:
    ALLOWED_CHATS = [c.strip() for c in _chat_env.split(",") if c.strip()]
else:
    _chat_id = _config.get("telegram_chat_id", "")
    ALLOWED_CHATS = [_chat_id] if _chat_id else []


def send_message(chat_id, text):
    """Send a Telegram message, auto-chunking at 4000 characters."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for i in range(0, len(text), 4000):
        chunk = text[i : i + 4000]
        data = json.dumps({"chat_id": int(chat_id), "text": chunk}).encode()
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if not result.get("ok"):
                print(f"Send failed: {result}", file=sys.stderr)
                return False
    return True


def main():
    # Parse input mode first so bare invocation prints usage
    if len(sys.argv) > 1 and sys.argv[1] == "--stdin":
        text = sys.stdin.read().strip()
    elif len(sys.argv) > 1 and sys.argv[1] == "-f":
        if len(sys.argv) < 3:
            print("Error: -f requires a file path", file=sys.stderr)
            sys.exit(1)
        with open(sys.argv[2]) as f:
            text = f.read().strip()
    elif len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        print(
            "Usage: notify.py <message> | -f <file> | --stdin", file=sys.stderr
        )
        sys.exit(1)

    if not text:
        print("Error: message content is empty", file=sys.stderr)
        sys.exit(1)

    if not BOT_TOKEN:
        print("Error: ASSISTANT_TELEGRAM_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    if not ALLOWED_CHATS:
        print("Error: no chat IDs configured. Set ASSISTANT_ALLOWED_CHATS env var or telegram_chat_id in config.json", file=sys.stderr)
        sys.exit(1)

    # Dedup check: skip identical content within 10-minute window
    if _check_dedup(text):
        print("Skipped: identical message sent within last 10 minutes", file=sys.stderr)
        sys.exit(0)

    # Send to all allowed chats
    ok = True
    for chat_id in ALLOWED_CHATS:
        if not send_message(chat_id, text):
            ok = False
            print(f"Send failed: chat_id={chat_id}", file=sys.stderr)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
