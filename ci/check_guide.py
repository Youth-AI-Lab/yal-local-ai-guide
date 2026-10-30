"""Does what the guide asks in the browser (part 3 steps 6-7, parts 4 to 6), through the API of
Open WebUI, with the same settings, and checks what the guide says should happen.

Phases, run in this order between the stages of run_guide.py:
    admin         part 3, steps 6-7: the administrator account, the settings of openwebui.env (on
                  the Raspberry Pi page, step 7 also sets Legacy and Builtin Tools off on the model)
    chatbot       parts 4 and 5: knowledge, chatbot with Legacy and num_ctx 8192, an answer with sources
    participants  part 6, after the stage "network": safety net of the base model, Public access,
                  a participant account, what it sees and what the base model answers it
    journal       part 3, step 4: no e-mail and no address in the journal of the service (Linux,
                  Raspberry Pi), or in ~/owui-local/open-webui.log, the log of owui-start.py (macOS,
                  Windows)

With the AI HAT+ 2 of the Raspberry Pi page (--os raspberry-pi-hat, or --server hailo), the model
server is hailo-ollama, and the same phases do what the section "With the AI HAT+ 2" asks:
    admin         part 3, step 6, then AI HAT+ 2 steps 8 and 9: the connection to hailo-ollama
                  replaces the one to Ollama; with the settings by default, Open WebUI sends its
                  tools and hailo-ollama refuses the question (HTTP 500); with Legacy and Builtin
                  Tools off, it accepts it
    chatbot       AI HAT+ 2 step 10: a chatbot without documents, with Legacy and Builtin Tools off,
                  whose question and answer fit in the 2,048 tokens of the AI HAT+ 2
    participants  part 6, as above, without documents: no tools reach hailo-ollama, the safety net
                  does, and hailo-ollama does not answer on the network address
    journal       as above, and no question of the group in the journal of hailo-ollama
In CI, GitHub has no AI HAT+ 2: what answers is ci/fake_hailo_ollama.py, a stand-in that answers
like hailo-ollama 5.1.1 and writes one line per request in CI_HAILO_LOG (never the text of a
question). The checks read what hailo-ollama received in that log: whether tools were sent, how many
tokens the question had (Qwen2 tokenizer), whether the instructions came first.

Usage: python3 ci/check_guide.py <phase> [--os linux|macos|windows|raspberry-pi|raspberry-pi-hat]
                                         [--server ollama|hailo]
(by default, the system it runs on, and hailo only for raspberry-pi-hat)

Needs KIT_DIR (a copy of the workshop kit: its summaries are the documents; not with hailo) and
OWUI_GUIDE_DIR (a copy of the Open WebUI guide: its filled example of instructions), and CI_HAILO_LOG
with hailo. Only the standard library.
"""
import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

URL = os.environ.get("OPENWEBUI_URL", "http://localhost:3000")
MODEL = os.environ.get("CI_MODEL", "qwen2.5:0.5b")
STATE = Path(os.environ.get("CI_STATE", Path.home() / ".cache" / "guide-ci" / "state.json"))
ADMIN = {"name": "Facilitator", "email": "facilitator@group.local", "password": "Ci-admin-pass-2026"}
PARTICIPANT = {"name": "test", "email": "test@group.local", "password": "Ci-test-pass-2026"}
DOCUMENTS = ["30-charente-maritime-vigilance-levels.md", "31-charente-maritime-fire-use-rules.md",
             "50-catalonia-pla-alfa.md", "90-contradiction.md"]
QUESTION = "What are the six fire vigilance levels in Charente-Maritime?"
SAFETY = ("You are not the group's chatbot. To any question, answer only: please choose the group's "
          "chatbot in the list.")
EVERYONE = [{"principal_type": "user", "principal_id": "*", "permission": "read"}]
CHATBOT_ID = "camp-fire-rules-test"
# Open WebUI's own tools add about 2,800 tokens to each question (measured on the guide's laptop with
# Open WebUI 0.11.4; TO BE COMPLETED: with 0.12.4, which offers the model more tools).
TOOLS_TOKENS = 1500
# The system of the guide's page that was followed (--os): by default, the one this runs on. A
# Raspberry Pi says linux: pass --os raspberry-pi or raspberry-pi-hat.
SYSTEM = {"darwin": "macos", "win32": "windows"}.get(sys.platform, "linux")
# The pages whose Open WebUI is a systemd service: its journal, and a restart that waits.
LINUX_LIKE = {"linux", "raspberry-pi", "raspberry-pi-hat"}
# The model server behind Open WebUI (--server): ollama, or hailo for hailo-ollama, the program of
# the AI HAT+ 2 (in CI, its stand-in ci/fake_hailo_ollama.py).
SERVER = "ollama"
HAILO_URL = os.environ.get("HAILO_URL", "http://127.0.0.1:8000")
# The log of the stand-in: one JSON line per request, never the text of a question.
HAILO_LOG = os.environ.get("CI_HAILO_LOG")
# The context of the models of the AI HAT+ 2, fixed when Hailo built them (MODELS.rst of
# hailo-ollama 5.1.1): the instructions, the conversation and the answer share it.
HAT_CONTEXT = 2048
# The longest answer CI asks for (max_tokens, num_predict for Ollama and hailo-ollama).
ANSWER_TOKENS = 400
HAT_QUESTION = "How can a youth group prevent forest fires during a camp?"

failures = []


def check(ok, what):
    print(("  ok    " if ok else "  FAIL  ") + what, flush=True)
    if not ok:
        failures.append(what)
    return ok


class Api:
    def __init__(self, token=""):
        self.token = token

    def request(self, method, path, body=None, query=None, raw=None, content_type=None, timeout=900):
        full = URL + (path if path.startswith(("/api/", "/openai/", "/ollama/")) else "/api/v1" + path)
        if query:
            full += "?" + urllib.parse.urlencode(query)
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        data = raw
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        elif content_type:
            headers["Content-Type"] = content_type
        req = urllib.request.Request(full, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{method} {path}: HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from None
        return json.loads(text) if text else None

    def try_request(self, *args, **kw):
        try:
            return self.request(*args, **kw)
        except RuntimeError as e:
            return e

    def chat(self, model, question, history=()):
        # The page of Open WebUI loads the list of models first (a new chatbot is unknown until then),
        # and sends a session id: without it, Open WebUI never offers its own tools to the model.
        self.request("GET", "/api/models")
        # CI only: the tiny model of CI sometimes writes without end until its window is full (seen on
        # ubuntu-24.04: "slot context shift" in Ollama's journal, then a 15-minute timeout). A limit on
        # the length of this answer (max_tokens, num_predict for Ollama) changes no setting of the
        # chatbot: the checks read the sources and the tokens sent, not a long answer.
        return self.request("POST", "/api/chat/completions", body={
            "model": model, "stream": False, "session_id": "ci-" + uuid.uuid4().hex[:8],
            "max_tokens": ANSWER_TOKENS, "messages": [*history, {"role": "user", "content": question}]})

    def upload(self, path):
        boundary = uuid.uuid4().hex
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
                "Content-Type: text/markdown\r\n\r\n").encode() + path.read_bytes() \
            + f"\r\n--{boundary}--\r\n".encode()
        return self.request("POST", "/files/", raw=body, query={"process": "true", "process_in_background": "false"},
                            content_type=f"multipart/form-data; boundary={boundary}")


def answer_of(data):
    msg = ((data.get("choices") or [{}])[0]).get("message", {})
    return msg.get("content") or ""


def prompt_tokens(data):
    usage = data.get("usage") or {}
    return usage.get("prompt_tokens") or usage.get("input_tokens") or usage.get("prompt_eval_count")


def source_files(data):
    names = []
    for src in data.get("sources") or []:
        for m in src.get("metadata") or []:
            name = m.get("source") or m.get("name")
            if name and name not in names:
                names.append(name)
    return names


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state))


def wait_ready(url=URL):
    for _ in range(120):
        try:
            urllib.request.urlopen(url + "/health", timeout=5)
            return
        except OSError:
            time.sleep(5)
    sys.exit(f"Open WebUI does not answer at {url}")


def network_address():
    """The address of this computer on its network, or None (no packet is sent: UDP has no handshake)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 9))  # an address reserved for documentation
            address = s.getsockname()[0]
    except OSError:
        return None
    return None if address.startswith("127.") else address


def wait_restarted():
    """macOS and Windows: the stage "network" may return before Open WebUI has started again.

    On Linux, systemctl restart waits for the old process to stop. launchctl and Task Scheduler may
    not: the old Open WebUI, for this computer only, could still answer on localhost. Open WebUI
    answers on the network address of the computer only once it listens on 0.0.0.0, that is once
    the new one is ready.
    """
    address = network_address()
    if address:
        print(f"waiting for Open WebUI on the network address {address}", flush=True)
        wait_ready(f"http://{address}:{urllib.parse.urlsplit(URL).port or 3000}")
    wait_ready()


def hailo_lines():
    """The complete lines of the log of the stand-in for hailo-ollama, as they are now."""
    try:
        with open(HAILO_LOG, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return []
    return text[:text.rfind("\n") + 1].splitlines()


def hailo_mark():
    """Where the log of the stand-in ends now: the requests after it are the next question's."""
    return len(hailo_lines())


def hailo_requests(mark, wait=0):
    """The questions (/api/chat, /api/generate) that hailo-ollama received after the mark.

    The stand-in may write its line just after its answer, once Open WebUI has passed it on: wait
    up to `wait` seconds for a first one, then a second more for any other.
    """
    deadline = time.monotonic() + wait
    settled = False
    while True:
        found = []
        for line in hailo_lines()[mark:]:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if str(entry.get("path", "")).split("?")[0] in ("/api/chat", "/api/generate"):
                found.append(entry)
        if not wait or settled or (not found and time.monotonic() >= deadline):
            return found
        if found:
            settled = True
        time.sleep(1 if found else 0.5)


def hailo_get(path):
    """A request straight to hailo-ollama, as the curl commands of the page."""
    with urllib.request.urlopen(HAILO_URL + path, timeout=30) as resp:
        return json.loads(resp.read().decode())


def hailo_turn(api, model, question, history=()):
    """One question through Open WebUI, and what hailo-ollama received for it."""
    mark = hailo_mark()
    try:
        data = api.chat(model, question, history)
    except RuntimeError as e:  # the checks then say what hailo-ollama received
        print(f"  info  Open WebUI shows: {str(e)[:160]}")
        data = {}
    return data, hailo_requests(mark, wait=10)


def most_tokens(entries):
    counts = [e["prompt_tokens"] for e in entries if isinstance(e.get("prompt_tokens"), int)]
    return max(counts) if counts else None


def check_hat_turn(data, entries, what):
    """What every question to the AI HAT+ 2 must show: an answer, no tools, and room in 2,048 tokens."""
    check(bool(answer_of(data).strip()), f"{what}: it answers: {answer_of(data)[:80]!r}")
    statuses = [e.get("status") for e in entries]
    check(bool(entries) and all(st == 200 for st in statuses),
          f"{what}: hailo-ollama accepts the question (HTTP {', '.join(map(str, statuses)) or 'nothing received'})")
    check(bool(entries) and not any(e.get("has_tools") for e in entries), f"{what}: no tools are sent to hailo-ollama")
    tokens = most_tokens(entries)
    counted = [e for e in entries if isinstance(e.get("prompt_tokens"), int)]
    how = "Qwen2 tokenizer" if counted and all(e.get("token_count") == "qwen2-tokenizer" for e in counted) else "estimated"
    check(tokens is not None and tokens + ANSWER_TOKENS <= HAT_CONTEXT,
          f"{what}: the question and an answer of up to {ANSWER_TOKENS} tokens fit in the "
          f"{HAT_CONTEXT:,} tokens of the AI HAT+ 2 ({tokens} tokens, {how})")
    return tokens


def edit_base_model(admin, **params):
    """The pencil on the line of the base model (Admin Panel > Settings > Models): Builtin Tools off
    in Capabilities, and these settings."""
    got = admin.try_request("GET", "/models/model", query={"id": MODEL})
    base = None if isinstance(got, RuntimeError) else got  # no row yet: the model was never edited
    form = {"id": MODEL, "name": MODEL, "base_model_id": None, "is_active": True,
            "meta": {**((base or {}).get("meta") or {}), "capabilities": {
                **(((base or {}).get("meta") or {}).get("capabilities") or {}), "builtin_tools": False}},
            "params": {**((base or {}).get("params") or {}), **params}}
    admin.request("POST", "/models/model/update" if base else "/models/create", body=form)


def ollama_program():
    """ollama, or on Windows where its installer puts it: a later step of CI does not get the PATH
    that the installer changed."""
    found = shutil.which("ollama")
    if not found and os.name == "nt":
        program = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
        found = str(program) if program.exists() else None
    return found or "ollama"


def phase_admin(state):
    print("Part 3, step 6: the administrator account")
    first = Api().request("POST", "/auths/signup", body=ADMIN)
    check(first.get("role") == "admin", "the first account becomes the administrator")
    admin = Api(first["token"])
    state["admin"] = first["token"]
    other = Api().try_request("POST", "/auths/signup", body=PARTICIPANT)
    check(isinstance(other, RuntimeError), "then the sign-ups are closed: a second account is refused")

    print("Part 3, step 4: the settings of openwebui.env")
    config = admin.request("GET", "/api/config")
    check(config.get("name", "").startswith("Group chatbots"), f"name of the site: {config.get('name')!r}")
    auth = admin.request("GET", "/auths/admin/config")
    check(auth.get("SHOW_ADMIN_DETAILS") is False, "the participants do not see the administrator's details")
    check(auth.get("JWT_EXPIRES_IN") == "12h", f"a sign-in lasts 12 hours ({auth.get('JWT_EXPIRES_IN')})")
    check(auth.get("ENABLE_SIGNUP") is False, "sign-ups closed")
    banners = admin.request("GET", "/configs/banners")
    check(any("personal information" in (b.get("content") or "") for b in banners), "the banner about personal information")
    arena = admin.request("GET", "/evaluations/config")
    check(arena.get("ENABLE_EVALUATION_ARENA_MODELS") is False, "no Arena Model")
    tasks = admin.request("GET", "/tasks/config")
    check(not tasks.get("ENABLE_TITLE_GENERATION") and not tasks.get("ENABLE_FOLLOW_UP_GENERATION"),
          "no hidden questions to the model (titles, follow-ups)")
    openai = admin.request("GET", "/openai/config")
    check(openai.get("ENABLE_OPENAI_API") is False, "no AI company: the OpenAI connection is off")

    if SERVER == "hailo":
        hat_connection(admin, state)
        return

    print("Part 3, step 7: the connection to Ollama")
    models = [m["id"] for m in admin.request("GET", "/api/models")["data"]]
    check(MODEL in models, f"{MODEL} is in the list of models ({', '.join(models)})")
    data = admin.chat(MODEL, "Hello, who are you?")
    check(bool(answer_of(data).strip()), f"it answers: {answer_of(data)[:80]!r}")
    tokens = prompt_tokens(data)
    print(f"  info  the base model with the settings by default received {tokens} tokens")
    state["tokens_default"] = tokens
    if SYSTEM == "raspberry-pi":
        pi_step7(admin, tokens)


def pi_step7(admin, default_tokens):
    """Raspberry Pi page, part 3, step 7: the two settings come before the first question, because
    its processor must read every token. The question above, with the settings by default, is only
    there to compare; the reader does not ask it."""
    print("Part 3, step 7, Raspberry Pi: Function Calling Legacy, Builtin Tools off")
    edit_base_model(admin, function_calling="legacy")
    row = admin.request("GET", "/models/model", query={"id": MODEL})
    check(row["params"].get("function_calling") == "legacy" and row["meta"]["capabilities"].get("builtin_tools") is False,
          "the model of the Raspberry Pi: Legacy, Builtin Tools off")
    data = admin.chat(MODEL, "Hello, who are you?")
    check(bool(answer_of(data).strip()), f"it answers: {answer_of(data)[:80]!r}")
    tokens = prompt_tokens(data)
    check(tokens is not None and tokens < TOOLS_TOKENS,
          f"no tools are sent to the model ({tokens} tokens, {default_tokens} with the settings by default)")


def hat_connection(admin, state):
    """AI HAT+ 2, steps 8 and 9 (part 3, step 7 is skipped: no Ollama in this job)."""
    print("AI HAT+ 2, step 8: connect Open WebUI to hailo-ollama")
    version = admin.request("POST", "/ollama/verify", body={"url": HAILO_URL}) or {}
    check(version.get("version") == "0.5.1", f"Open WebUI reaches hailo-ollama: version {version.get('version')}")
    before = admin.request("GET", "/ollama/config")
    print(f"  info  the connection before: {before.get('OLLAMA_BASE_URLS')}")
    admin.request("POST", "/ollama/config/update", body={
        "ENABLE_OLLAMA_API": True, "OLLAMA_BASE_URLS": [HAILO_URL], "OLLAMA_API_CONFIGS": {}})
    after = admin.request("GET", "/ollama/config")
    check(after.get("ENABLE_OLLAMA_API") is True and after.get("OLLAMA_BASE_URLS") == [HAILO_URL],
          f"hailo-ollama replaces Ollama: {after.get('OLLAMA_BASE_URLS')}")
    served = [m["id"] for m in admin.request("GET", "/api/models")["data"] if m.get("owned_by") == "ollama"]
    check(served == [MODEL], f"the list shows {MODEL}, and nothing else from Ollama ({', '.join(served) or 'nothing'})")

    print("AI HAT+ 2, step 9: why the model needs two changes")
    mark = hailo_mark()
    try:
        admin.chat(MODEL, "Hello, who are you?")
    except RuntimeError as e:
        print(f"  info  Open WebUI shows: {str(e)[:160]}")
    refused = [e for e in hailo_requests(mark, wait=10) if e.get("has_tools")]
    check(any(e.get("status") == 500 for e in refused),
          "with the default settings, Open WebUI 0.12.4 sends its tools, and hailo-ollama 5.1.1 refuses "
          "them: HTTP 500, as on Hailo's forum"
          + (f" ({refused[0].get('error')})" if refused and refused[0].get("error") else ""))

    print("AI HAT+ 2, step 9: Function Calling Legacy, Builtin Tools off")
    edit_base_model(admin, function_calling="legacy")
    row = admin.request("GET", "/models/model", query={"id": MODEL})
    check(row["params"].get("function_calling") == "legacy" and row["meta"]["capabilities"].get("builtin_tools") is False,
          "the model of the AI HAT+ 2: Legacy, Builtin Tools off")
    state["hailo_mark_ok"] = hailo_mark()
    data, entries = hailo_turn(admin, MODEL, "Hello, who are you?")
    state["tokens_default"] = check_hat_turn(data, entries, f"{MODEL} with Legacy and Builtin Tools off")


def phase_chatbot(state):
    if SERVER == "hailo":
        hat_chatbot(state)
        return
    admin = Api(state["admin"])
    kit = Path(os.environ["KIT_DIR"])
    example = Path(os.environ["OWUI_GUIDE_DIR"]) / "templates" / "examples" / "topic-assistant.example.md"
    print("Part 4: the documents")
    knowledge = admin.request("POST", "/knowledge/create",
                              body={"name": "Wildfire test", "description": "Test documents"})
    for name in DOCUMENTS:
        file = admin.upload(kit / "summaries" / name)
        admin.request("POST", f"/knowledge/{knowledge['id']}/file/add", body={"file_id": file["id"]})
    files = admin.request("GET", f"/knowledge/{knowledge['id']}/files", query={"page": 1, "limit": 50})
    check(len(files.get("items", [])) == len(DOCUMENTS), f"{len(DOCUMENTS)} documents in the knowledge, read offline")
    state["knowledge"] = knowledge["id"]

    print("Part 4: the chatbot (Legacy, num_ctx 8192)")
    text = example.read_text(encoding="utf-8")
    instructions = text.split("\n---\n", 1)[1].strip()
    admin.request("POST", "/models/create", body={
        "id": CHATBOT_ID, "name": "Camp fire rules (test)", "base_model_id": MODEL, "is_active": True,
        "meta": {"description": "Test chatbot", "knowledge": [{
            "id": knowledge["id"], "name": knowledge["name"], "description": "", "type": "collection"}]},
        "params": {"system": instructions, "function_calling": "legacy", "num_ctx": 8192},
        "access_grants": []})

    print("Part 4: what you should see")
    started = time.monotonic()
    data = admin.chat(CHATBOT_ID, QUESTION)
    seconds = time.monotonic() - started
    files = source_files(data)
    # The guide promises sources, not a given document: a tiny model rewrites the question its own way.
    check(bool(files), f"the answer has its sources: {', '.join(files) or 'none'}")
    tokens = prompt_tokens(data)
    check(tokens is not None and tokens < 8192, f"the question fits in 8192 tokens ({tokens})")
    print(f"  info  answer in {seconds:.0f} s on the processor of CI: {answer_of(data)[:100]!r}")
    ps = subprocess.run([ollama_program(), "ps"], capture_output=True, text=True).stdout
    check("8192" in ps, "ollama ps: CONTEXT 8192")
    print("  " + ps.replace("\n", "\n  "))


def hat_chatbot(state):
    """AI HAT+ 2, step 10: part 4 without documents (no knowledge, no num_ctx: the context is fixed)."""
    admin = Api(state["admin"])
    example = Path(os.environ["OWUI_GUIDE_DIR"]) / "templates" / "examples" / "topic-assistant.example.md"
    print("AI HAT+ 2, step 10: a chatbot without documents (Legacy, Builtin Tools off)")
    text = example.read_text(encoding="utf-8")
    instructions = text.split("\n---\n", 1)[1].strip()
    admin.request("POST", "/models/create", body={
        "id": CHATBOT_ID, "name": "Camp fire rules (test)", "base_model_id": MODEL, "is_active": True,
        "meta": {"description": "Test chatbot", "capabilities": {"builtin_tools": False}},
        "params": {"system": instructions, "function_calling": "legacy"},
        "access_grants": []})

    print("AI HAT+ 2, step 10: what you should see")
    started = time.monotonic()
    data, entries = hailo_turn(admin, CHATBOT_ID, HAT_QUESTION)
    seconds = time.monotonic() - started
    chats = [e for e in entries if str(e.get("path", "")).startswith("/api/chat")]
    if len(chats) != 1:
        print(f"  info  {len(chats)} requests to /api/chat for one question (one expected: no hidden question)")
    check(bool(entries) and all(e.get("system_first") for e in entries),
          "the chatbot's instructions reach the model first")
    tokens = check_hat_turn(data, entries, "the chatbot")
    print(f"  info  answer in {seconds:.0f} s from the stand-in of CI (not a model): {answer_of(data)[:100]!r}")
    loaded = [m.get("name") or m.get("model") for m in hailo_get("/api/ps").get("models") or []]
    check(MODEL in loaded, f"hailo-ollama's /api/ps: {MODEL} is loaded ({', '.join(map(str, loaded)) or 'nothing'})")

    # Info only: the whole conversation is sent again with each question.
    answer = answer_of(data)
    history = [{"role": "user", "content": HAT_QUESTION}, {"role": "assistant", "content": answer},
               {"role": "user", "content": "What should we do if we see smoke?"},
               {"role": "assistant", "content": answer}]
    mark = hailo_mark()
    try:
        admin.chat(CHATBOT_ID, "Who do we call in an emergency?", history)
    except RuntimeError as e:
        print(f"  info  the third question failed: {str(e)[:160]}")
    later = most_tokens(hailo_requests(mark, wait=10))
    print(f"  info  the third question of a conversation: {later} tokens, the first {tokens} (the answers "
          "of the stand-in are short; a real model's are longer)")


def phase_participants(state):
    if SYSTEM not in LINUX_LIKE:
        wait_restarted()
    wait_ready()
    admin = Api(state["admin"])
    check(isinstance(admin.try_request("GET", "/auths/"), dict),
          "the restart of part 6, step 1, signs nobody out")
    print("Part 6, before the first session, step 3: the base model")
    edit_base_model(admin, system=SAFETY, function_calling="legacy")
    row = admin.request("GET", "/models/model", query={"id": MODEL})
    row["meta"]["hidden"] = True
    admin.request("POST", "/models/model/update", body=row)
    admin.request("POST", "/models/model/access/update", body={"id": MODEL, "name": MODEL, "access_grants": EVERYONE})
    row = admin.request("GET", "/models/model", query={"id": MODEL})
    check(row["meta"].get("hidden") is True, "hidden")
    check(row["params"].get("system") == SAFETY and row["params"].get("function_calling") == "legacy"
          and row["meta"]["capabilities"].get("builtin_tools") is False,
          "the safety net is still there after Hide Model and Make Public")

    print("Part 6, before each session, step 4: Public access")
    # Access has its own call, as the window Access of the page: since Open WebUI 0.12.4, an update
    # of the model (Save & Update) no longer changes who can read it.
    chatbot = admin.request("GET", "/models/model", query={"id": CHATBOT_ID})
    admin.request("POST", "/models/model/access/update",
                  body={"id": CHATBOT_ID, "name": chatbot["name"], "access_grants": EVERYONE})
    if SERVER != "hailo":  # no documents on the AI HAT+ 2
        admin.request("POST", f"/knowledge/{state['knowledge']}/access/update", body={"access_grants": EVERYONE})

    print("Part 6, during the session: sign-ups, a participant")
    config = admin.request("GET", "/auths/admin/config")
    config.update({"ENABLE_SIGNUP": True, "DEFAULT_USER_ROLE": "user"})
    admin.request("POST", "/auths/admin/config", body=config)
    signup = Api().request("POST", "/auths/signup", body=PARTICIPANT)
    user = Api(signup["token"])
    chat = (signup.get("permissions") or {}).get("chat") or {}
    hidden = ("system_prompt", "params", "controls", "file_upload", "temporary", "share")
    check(all(chat.get(k) is False for k in hidden),
          "the participants do not see the buttons to change a chatbot, upload files, share, or chat "
          f"without saving ({', '.join(f'{k}={chat.get(k)}' for k in hidden)})")
    visible = [m["id"] for m in user.request("GET", "/api/models")["data"]
               if not ((m.get("info") or {}).get("meta") or {}).get("hidden")]
    check(visible == [CHATBOT_ID], f"the participant's list shows only the chatbot ({', '.join(visible)})")
    if SERVER == "hailo":
        hat_participant(user, state)
    else:
        data = user.chat(CHATBOT_ID, QUESTION)
        files = source_files(data)
        check(bool(files), f"the participant's answer has its sources: {', '.join(files) or 'none'}")
        data = user.chat(MODEL, "Hello")
        tokens = prompt_tokens(data)
        check(tokens is not None and tokens < TOOLS_TOKENS,
              f"?model={MODEL}: no tools are sent to the base model ({tokens} tokens, "
              f"{state.get('tokens_default')} before the safety net)")
        answer = answer_of(data)
        print(f"  info  the base model answered the participant: {answer[:120]!r}"
              + ("" if "choose" in answer.lower() else "  (a tiny model may not follow its instruction)"))
    details = user.try_request("GET", "/auths/admin/details")
    check(isinstance(details, RuntimeError) or not (details or {}).get("email"),
          "the participant does not get the administrator's e-mail")
    config["ENABLE_SIGNUP"] = False
    admin.request("POST", "/auths/admin/config", body=config)
    other = Api().try_request("POST", "/auths/signup", body={**PARTICIPANT, "email": "late@group.local"})
    check(isinstance(other, RuntimeError), "after the session: sign-ups closed again")
    if SERVER == "hailo":
        hat_session_end(state)


def hat_participant(user, state):
    """Part 6 on the AI HAT+ 2: the participant's chatbot and the safety net, without documents."""
    data, entries = hailo_turn(user, CHATBOT_ID, HAT_QUESTION)
    check_hat_turn(data, entries, "the participant's chatbot")
    data, entries = hailo_turn(user, MODEL, "Hello")
    check(bool(entries) and all(e.get("system_first") for e in entries),
          f"?model={MODEL}: the safety net comes first in what hailo-ollama receives")
    tokens = check_hat_turn(data, entries, f"?model={MODEL}")
    print(f"  info  {tokens} tokens with the safety net, {state.get('tokens_default')} before it")
    answer = answer_of(data)
    check("choose the group's chatbot" in answer.lower(),
          f"the safety net reaches the model (the stand-in repeats its instruction; a real {MODEL} is "
          f"not tested): {answer[:100]!r}")
    address = network_address()
    port = urllib.parse.urlsplit(HAILO_URL).port or 8000
    if not address:
        print("  info  no network address: the check of hailo-ollama from the network is skipped")
        return
    try:
        socket.create_connection((address, port), timeout=5).close()
        reached = True
    except OSError:
        reached = False
    check(not reached, f"hailo-ollama does not answer on the network address ({address}:{port})")


def hat_session_end(state):
    """Every question since step 9 reached hailo-ollama without tools, accepted, within 2,048 tokens."""
    since = hailo_requests(state.get("hailo_mark_ok", 0))
    bad = [e for e in since if e.get("has_tools") or e.get("status") != 200 or e.get("over_context")]
    check(bool(since) and not bad,
          f"since step 9 of the AI HAT+ 2: {len(since)} questions to hailo-ollama, none with tools, "
          f"none refused, none over {HAT_CONTEXT:,} tokens ({len(bad)} wrong)")
    for e in bad[:5]:
        print(f"        {e.get('path')} HTTP {e.get('status')} tools={e.get('has_tools')} "
              f"tokens={e.get('prompt_tokens')} {e.get('error') or ''}")
    print(f"  info  the longest question: {most_tokens(since)} tokens of {HAT_CONTEXT:,}")


def phase_journal(state):
    if SYSTEM in LINUX_LIKE:
        print("Part 3, step 4: the journal of the service")
        out = subprocess.run(["sudo", "journalctl", "-u", "owui-local", "--no-pager"],
                             capture_output=True, text=True).stdout
        where = "the journal"
    else:
        log = Path.home() / "owui-local" / "open-webui.log"
        print(f"Part 3, step 4: the log of Open WebUI, {log}")
        if not check(log.exists(), f"{log} exists"):
            return
        out = log.read_text(encoding="utf-8", errors="replace")
        where = "the log"
    leaks = [l for l in out.splitlines() if "@group.local" in l or "POST /" in l]
    check(not leaks, f"no e-mail and no address in {where} ({len(out.splitlines())} lines read)")
    for line in leaks[:5]:
        print("        " + line[:160])
    if SERVER == "hailo":
        hat_journal()


def hat_journal():
    """AI HAT+ 2, step 5: StandardOutput=null keeps the questions out of the journal of hailo-ollama."""
    print("AI HAT+ 2, step 5: the journal of hailo-ollama")
    out = subprocess.run(["sudo", "journalctl", "-u", "hailo-ollama", "--no-pager"],
                         capture_output=True, text=True).stdout
    words = ("got prompt", "<|im_start|>", HAT_QUESTION, "@group.local")
    leaks = [l for l in out.splitlines() if any(w in l for w in words)]
    check(not leaks, f"no question of the group in the journal of hailo-ollama ({len(out.splitlines())} lines read)")
    for line in leaks[:5]:
        print("        " + line[:160])
    # The journal is clean because questions were hidden, not because none was asked.
    answered = [e for e in hailo_requests(0)
                if str(e.get("path", "")).startswith("/api/chat") and e.get("status") == 200]
    check(bool(answered), f"while hailo-ollama answered {len(answered)} questions (the log of CI)")


def main():
    global SYSTEM, SERVER
    phases = {"admin": phase_admin, "chatbot": phase_chatbot, "participants": phase_participants,
              "journal": phase_journal}
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=list(phases))
    parser.add_argument("--os", choices=["linux", "macos", "windows", "raspberry-pi", "raspberry-pi-hat"],
                        default=SYSTEM)
    parser.add_argument("--server", choices=["ollama", "hailo"],
                        help="the model server (by default hailo for raspberry-pi-hat, otherwise ollama)")
    args = parser.parse_args()
    SYSTEM, phase = args.os, args.phase
    SERVER = args.server or ("hailo" if SYSTEM == "raspberry-pi-hat" else "ollama")
    if SERVER == "hailo" and not HAILO_LOG:
        sys.exit("--server hailo needs CI_HAILO_LOG, the log of ci/fake_hailo_ollama.py (see guide.yml)")
    wait_ready()
    state = load_state()
    phases[phase](state)
    save_state(state)
    if failures:
        sys.exit(f"{len(failures)} check(s) failed in phase {phase}")


if __name__ == "__main__":
    main()
