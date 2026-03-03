#!/usr/bin/env python3
"""Telegram Bot — multi-turn conversations with Claude Code.

Polling mode, zero external dependencies (Python stdlib only).

Features:
- Multi-turn: messages within SESSION_TIMEOUT share conversation context
- Session digest: expired sessions get summarized to MEMORY.md
- Commands: /opus, /sonnet, /new, /status
- Self-update detection: graceful restart when this file is modified
- Crash protection: persisted retry counts, rapid restart cooldown
- Long-term memory: optional vector+keyword search (graceful degradation)
- Multi-agent: AGENT_DIR env var selects which agent directory to use
"""

import atexit, http.client, json, os, signal, socket, subprocess
import sys, threading, time, urllib.error, urllib.request

# --- Config ---

SCRIPT_PATH = os.path.abspath(__file__)
TOOLS_DIR = os.path.dirname(SCRIPT_PATH)

def _load_config():
    try:
        with open(os.path.join(TOOLS_DIR, "config.json")) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

_cfg = _load_config()

AGENT_DIR = os.environ.get("AGENT_DIR", _cfg.get("assistant_dir", "assistant"))
KB_DIR = os.path.abspath(os.path.join(TOOLS_DIR, "..", ".."))
AGENT_NAME = os.path.basename(AGENT_DIR)

BOT_TOKEN = os.environ.get("ASSISTANT_TELEGRAM_TOKEN") or _cfg.get("telegram_token", "")
_chat_env = os.environ.get("ASSISTANT_ALLOWED_CHATS", "")
ALLOWED_CHATS = (set(c.strip() for c in _chat_env.split(",") if c.strip()) if _chat_env
                 else ({_cfg["telegram_chat_id"]} if _cfg.get("telegram_chat_id") else set()))

CLAUDE_BIN = os.environ.get("CLAUDE_BIN", os.path.expanduser("~/.local/bin/claude"))
DEFAULT_MODEL = _cfg.get("default_model", "sonnet")
BUDGET = {k: str(v) for k, v in _cfg.get("budget_usd", {"sonnet": "2.00", "opus": "5.00"}).items()}
SESSION_TIMEOUT = int(_cfg.get("session_timeout_minutes", 30)) * 60

LOGS_DIR = os.path.join(TOOLS_DIR, "logs")
LOG_FILE = os.path.join(LOGS_DIR, "telegram.log")
SESSIONS_FILE = os.path.join(LOGS_DIR, "telegram-sessions.json")
OFFSET_FILE = os.path.join(LOGS_DIR, "telegram-offset.json")
RETRY_FILE = os.path.join(LOGS_DIR, "telegram-retry-counts.json")
PID_FILE = os.path.join(LOGS_DIR, ".telegram-bot.pid")
RESTART_MARKER = os.path.join(LOGS_DIR, ".telegram-restart-pending")
RESTART_HIST = os.path.join(LOGS_DIR, ".telegram-last-start")

BOT_START_MTIME = os.path.getmtime(SCRIPT_PATH)
BOT_START_TIME = time.time()
MAX_RETRY = 3

# --- Logging ---

def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, file=sys.stderr)
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

# --- JSON helpers ---

def _rjson(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}

def _wjson(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- Long-term Memory (optional) ---

_mem_store = None
_mem_done = False
_mem_lock = threading.Lock()

def _init_memory():
    global _mem_store, _mem_done
    if _mem_done:
        return _mem_store
    with _mem_lock:
        if _mem_done:
            return _mem_store
        venv = os.path.join(TOOLS_DIR, "memory-venv")
        if os.path.exists(venv):
            lib = os.path.join(venv, "lib")
            if os.path.exists(lib):
                for d in os.listdir(lib):
                    if d.startswith("python"):
                        sp = os.path.join(lib, d, "site-packages")
                        if os.path.exists(sp) and sp not in sys.path:
                            sys.path.insert(0, sp)
        if TOOLS_DIR not in sys.path:
            sys.path.insert(0, TOOLS_DIR)
        try:
            import memory_store
            s = memory_store.get_store()
            _mem_store = s if s.available else None
        except Exception as e:
            log(f"Long-term memory unavailable: {e}")
            _mem_store = None
        _mem_done = True
    return _mem_store

def memory_recall(query, agent=None):
    """Recall relevant memories for prompt injection."""
    store = _init_memory()
    if not store:
        return ""
    scopes = ["global"] + ([agent] if agent and agent != "global" else [])
    try:
        return store.format_recall(store.recall(query, top_k=5, scopes=scopes))
    except Exception:
        return ""

_TRIVIAL = {"ok","yes","no","sure","thanks","thx","good","nice","cool","go","yep","do it"}

def memory_capture_bg(user_msg, bot_resp, agent=None):
    """Background capture of conversation into long-term memory."""
    def _do():
        store = _init_memory()
        if not store:
            return
        s = user_msg.strip().lower().rstrip(".!?")
        if s in _TRIVIAL or s.startswith("/"):
            return
        if len(user_msg) < 5 and len(bot_resp) < 50:
            return
        if not bot_resp or len(bot_resp) < 20:
            return
        try:
            store.capture(user_msg[:1000], bot_response=bot_resp[:1000],
                          scope=agent or "global", agent=agent or AGENT_NAME,
                          source="telegram")
        except Exception:
            pass
    threading.Thread(target=_do, daemon=True).start()

# --- Telegram API ---

def tg_api(method, _timeout=60, **params):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = json.dumps(params).encode()
    req = urllib.request.Request(url, data=data,
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=_timeout) as resp:
        return json.loads(resp.read())

def get_updates(offset=None):
    p = {"timeout": 30, "allowed_updates": ["message"]}
    if offset is not None:
        p["offset"] = offset
    return tg_api("getUpdates", **p)

def send_message(chat_id, text):
    for i in range(0, len(text), 4000):
        tg_api("sendMessage", chat_id=int(chat_id), text=text[i:i+4000])

def send_typing(chat_id):
    try:
        tg_api("sendChatAction", _timeout=5, chat_id=int(chat_id), action="typing")
    except Exception:
        pass

# --- Offset ---

def load_offset():
    return _rjson(OFFSET_FILE, {}).get("offset")

def save_offset(offset):
    _wjson(OFFSET_FILE, {"offset": offset})

# --- Crash Protection ---

def increment_retry(uid):
    counts = _rjson(RETRY_FILE, {})
    now = time.time()
    counts = {k: v for k, v in counts.items() if now - v.get("ts", 0) < 3600}
    key = str(uid)
    e = counts.get(key, {"count": 0, "ts": now})
    e["count"] += 1
    e["ts"] = now
    counts[key] = e
    _wjson(RETRY_FILE, counts)
    return e["count"]

def check_rapid_restart():
    now = time.time()
    d = _rjson(RESTART_HIST, {"ts": 0, "count": 0})
    c = d.get("count", 0) + 1 if now - d.get("ts", 0) < 30 else 1
    _wjson(RESTART_HIST, {"ts": now, "count": c})
    return c >= 5

# --- PID Lock ---

def acquire_pid_lock():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                old = int(f.read().strip())
            os.kill(old, 0)
            return False
        except (ProcessLookupError, ValueError):
            pass
        except PermissionError:
            return False
    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    return True

def release_pid_lock():
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                if int(f.read().strip()) == os.getpid():
                    os.remove(PID_FILE)
    except Exception:
        pass

# --- Self-Update ---

def bot_file_changed():
    try:
        return os.path.getmtime(SCRIPT_PATH) != BOT_START_MTIME
    except OSError:
        return False

def graceful_restart():
    log("Bot script updated, restarting...")
    try:
        _wjson(RESTART_MARKER, {"ts": time.time()})
    except Exception:
        pass
    sys.exit(0)

def check_restart_marker():
    try:
        d = _rjson(RESTART_MARKER)
        if not d:
            return
        os.remove(RESTART_MARKER)
        if time.time() - d.get("ts", 0) < 60:
            log("Restarted after code update")
            for cid in ALLOWED_CHATS:
                try:
                    send_message(cid, "Bot restarted with updated code.")
                except Exception:
                    pass
    except Exception:
        pass

# --- Sessions ---

def get_session(chat_id):
    """Returns (session_id, is_expired, session_data)."""
    s = _rjson(SESSIONS_FILE, {}).get(str(chat_id))
    if not s or not s.get("session_id"):
        return None, False, {}
    return s["session_id"], time.time() - s.get("last_active", 0) >= SESSION_TIMEOUT, s

def save_session(chat_id, sid, inc_turn=False):
    sessions = _rjson(SESSIONS_FILE, {})
    key = str(chat_id)
    now = time.time()
    if key not in sessions or sessions[key].get("session_id") != sid:
        sessions[key] = {"session_id": sid, "started": now, "turns": 0}
    sessions[key].update({"session_id": sid, "last_active": now})
    if inc_turn:
        sessions[key]["turns"] = sessions[key].get("turns", 0) + 1
    _wjson(SESSIONS_FILE, sessions)

def clear_session(chat_id):
    sessions = _rjson(SESSIONS_FILE, {})
    sessions.pop(str(chat_id), None)
    _wjson(SESSIONS_FILE, sessions)

# --- Session Prompt ---

def _load_session_prompt():
    # Look in current agent dir first, then fall back to primary agent's tools/
    candidates = [
        os.path.join(KB_DIR, AGENT_DIR, "tools", "session-prompt.md"),
        os.path.join(KB_DIR, AGENT_DIR, "session-prompt.md"),
        os.path.join(TOOLS_DIR, "session-prompt.md"),  # primary agent fallback
    ]
    for path in candidates:
        try:
            with open(path) as f:
                return f.read()
        except FileNotFoundError:
            continue
    return None

# --- Claude CLI ---

def run_claude(prompt, model=None, resume_id=None):
    """Returns (response_text, session_id). (None, None) on resume failure."""
    model = model or DEFAULT_MODEL
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    env.pop("CLAUDECODE", None)
    cmd = [CLAUDE_BIN, "-p", prompt, "--dangerously-skip-permissions",
           "--max-budget-usd", BUDGET.get(model, "2.00"),
           "--model", model, "--output-format", "json"]
    if resume_id:
        cmd += ["--resume", resume_id]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           cwd=KB_DIR, env=env, timeout=900,
                           start_new_session=True)
        if r.returncode != 0:
            err = (r.stderr[:300] or r.stdout[:300] or "(empty)").strip()
            log(f"Claude CLI failed (exit={r.returncode}): {err}")
            if resume_id:
                return None, None
            return f"(Claude error exit={r.returncode}: {err[:100]})", ""
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            return (r.stdout.strip() or r.stderr.strip() or "(parse error)"), ""
        text = data.get("result", "")
        sid = (data.get("session_id") or data.get("sessionId")
               or data.get("conversation_id") or data.get("conversationId") or "")
        if data.get("is_error"):
            if resume_id:
                return None, None
            return text or "(Claude error)", sid
        if not text:
            text = f"(Processed, no text. cost=${data.get('cost_usd', '?')})"
        return text, sid
    except subprocess.TimeoutExpired:
        return "(15 min timeout exceeded)", ""
    except Exception as e:
        return f"(Error: {e})", ""

# --- Session Digest ---

def digest_session_bg(sid, chat_id, sdata):
    def _run():
        started = sdata.get("started")
        hm = time.strftime("%H:%M", time.localtime(started)) if started else "?"
        today, month = time.strftime("%Y-%m-%d"), time.strftime("%Y-%m")
        prompt = (
            "This Telegram session has expired (idle timeout). Please:\n"
            f"1. Review conversation history.\n"
            f"2. If important decisions/TODOs/unfinished work exist, "
            f"update {AGENT_DIR}/MEMORY.md (tag #P1/#P2 @{today}).\n"
            f"3. Write summary to {AGENT_DIR}/activity-log/{month}/{today}.md "
            f"under: ## {hm} Telegram conversation\n"
            "4. Return 1-3 sentence summary (or 'No record needed' if trivial).\n")
        try:
            summary, _ = run_claude(prompt, DEFAULT_MODEL, sid)
            log(f"Session digest: {(summary or '?')[:120]}")
        except Exception as e:
            log(f"Session digest failed: {e}")
    threading.Thread(target=_run, daemon=True).start()

# --- Commands ---

def parse_command(text):
    """Returns (command, model, clean_message)."""
    s = text.strip()
    if s == "/new":     return "new", DEFAULT_MODEL, ""
    if s == "/status":  return "status", DEFAULT_MODEL, ""
    if s.startswith("/opus"):   return "message", "opus", s[5:].strip() or "(empty)"
    if s.startswith("/sonnet"): return "message", "sonnet", s[7:].strip() or "(empty)"
    return "message", DEFAULT_MODEL, text

# --- Status ---

def handle_status(chat_id):
    lines = []
    sid, expired, sd = get_session(chat_id)
    if sid and not expired:
        t = sd.get("turns", 0)
        age = int((time.time() - sd.get("started", 0)) / 60)
        idle = int((time.time() - sd.get("last_active", 0)) / 60)
        lines.append(f"Session: {t} turns | {age}m old | idle {idle}m")
    else:
        lines.append("Session: none active")
    up = int(time.time() - BOT_START_TIME)
    lines.append(f"Uptime: {up//3600}h {(up%3600)//60}m" if up >= 3600
                 else f"Uptime: {up//60}m")
    try:
        with open(os.path.join(KB_DIR, AGENT_DIR, "MEMORY.md")) as f:
            lines.append(f"MEMORY.md: {len(f.readlines())}/200 lines")
    except Exception:
        lines.append("MEMORY.md: unavailable")
    try:
        td = os.path.join(KB_DIR, AGENT_DIR, "tasks", "in-progress")
        if os.path.isdir(td):
            tasks = [f for f in os.listdir(td) if f.endswith(".md")]
            lines.append(f"Tasks: {len(tasks)}")
            for t in tasks[:5]:
                lines.append(f"  - {t[:-3]}")
    except Exception:
        pass
    lines.append(f"Model: {DEFAULT_MODEL}")
    send_message(chat_id, "\n".join(lines))

# --- Message Handler ---

def _new_session(message, chat_id, model):
    session_prompt = _load_session_prompt()
    if not session_prompt:
        return f"(Error: session-prompt.md not found in {AGENT_DIR})", ""
    prompt = session_prompt.replace("{message}", message)
    recalled = memory_recall(message, agent=AGENT_NAME)
    if recalled:
        prompt += f"\n\n---\n{recalled}"
    resp, sid = run_claude(prompt, model)
    if sid:
        save_session(chat_id, sid, inc_turn=True)
        log(f"New session: {sid[:12]}...")
    else:
        log("Warning: no session_id, multi-turn may not work")
    return resp, sid

def handle_message(chat_id, text):
    cmd, model, clean = parse_command(text)
    if cmd == "status":
        handle_status(chat_id)
        return
    if cmd == "new":
        sid, _, sd = get_session(chat_id)
        if sid:
            digest_session_bg(sid, chat_id, sd)
        clear_session(chat_id)
        send_message(chat_id, "New conversation started.")
        return

    stop = threading.Event()
    def _hb():
        while not stop.is_set():
            send_typing(chat_id)
            time.sleep(4)
    hb = threading.Thread(target=_hb, daemon=True)
    hb.start()

    try:
        sid, expired, sd = get_session(chat_id)
        if sid and expired:
            digest_session_bg(sid, chat_id, sd)
            clear_session(chat_id)
            sid = None
        if sid:
            log(f"Resuming {sid[:12]}... (turn {sd.get('turns',0)+1})")
            prompt = clean
            recalled = memory_recall(clean, agent=AGENT_NAME)
            if recalled:
                prompt += f"\n\n---\n{recalled}"
            resp, new_sid = run_claude(prompt, model, sid)
            if resp is None:
                log("Resume failed, new session")
                clear_session(chat_id)
                resp, new_sid = _new_session(clean, chat_id, model)
                if resp and not resp.startswith("("):
                    resp = "(session reset)\n" + resp
            if new_sid or sid:
                save_session(chat_id, new_sid or sid, inc_turn=True)
        else:
            resp, _ = _new_session(clean, chat_id, model)
        send_message(chat_id, resp)
        log(f"Reply [{model}]: {resp[:80]}...")
        memory_capture_bg(clean, resp, agent=AGENT_NAME)
    except Exception as e:
        log(f"Handler error: {e}")
        send_message(chat_id, f"Error: {str(e)[:200]}\n\nTry /new")
    finally:
        stop.set()
        hb.join(timeout=1)

# --- Main ---

def main():
    if not BOT_TOKEN:
        print("Error: set ASSISTANT_TELEGRAM_TOKEN or telegram_token in config.json",
              file=sys.stderr)
        sys.exit(1)
    if not acquire_pid_lock():
        log("Aborted: another instance running (PID lock)")
        sys.exit(1)
    atexit.register(release_pid_lock)

    mem = _init_memory()
    log(f"Long-term memory {'loaded' if mem else 'not available (optional)'}")
    log(f"Bot started (agent={AGENT_NAME}, timeout={SESSION_TIMEOUT}s, chats={ALLOWED_CHATS or 'any'})")
    check_restart_marker()

    if check_rapid_restart():
        log("Rapid restart loop (5+ in 30s), cooldown 60s")
        for cid in ALLOWED_CHATS:
            try: send_message(cid, "Restart loop detected, cooling down 60s.")
            except Exception: pass
        time.sleep(60)

    offset = load_offset()
    if offset:
        log(f"Offset from disk: {offset}")
    errs = 0

    while True:
        try:
            updates = get_updates(offset)
            errs = 0
            for u in updates.get("result", []):
                uid = u["update_id"]
                offset = uid + 1
                save_offset(offset)

                if increment_retry(uid) > MAX_RETRY:
                    log(f"Skip update_id={uid} (too many retries)")
                    continue

                msg = u.get("message", {})
                cid = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "") or msg.get("caption", "")
                date = msg.get("date", 0)
                sender = msg.get("from", {}).get("first_name", "?")

                if not text:
                    continue
                if date and date < BOT_START_TIME and time.time() - date > 300:
                    log(f"Skip stale msg ({int(time.time()-date)}s): {text[:40]}")
                    continue
                if ALLOWED_CHATS and cid not in ALLOWED_CHATS:
                    log(f"Rejected: cid={cid} sender={sender}")
                    continue
                if not ALLOWED_CHATS:
                    send_message(cid, f"Your chat_id is {cid}. Add to config.")
                    continue

                wait = time.time() - date if date else 0
                if wait > 60:
                    send_message(cid, f"Queued {int(wait/60)}m, processing now.")

                log(f"Recv: {sender} ({cid}): {text[:80]}")
                handle_message(cid, text)

                if bot_file_changed():
                    graceful_restart()

            if bot_file_changed():
                graceful_restart()

        except (urllib.error.URLError, http.client.HTTPException,
                ConnectionError, socket.timeout, OSError) as e:
            errs += 1
            if isinstance(e, urllib.error.HTTPError) and e.code == 409:
                log("409 Conflict: another instance polling")
                d = load_offset()
                if d and d != offset:
                    offset = d
            w = min(30, 2 ** errs)
            log(f"Network error: {e}, retry {w}s")
            time.sleep(w)
        except Exception as e:
            errs += 1
            w = min(30, 2 ** errs)
            log(f"Error: {e}, retry {w}s")
            time.sleep(w)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    main()
