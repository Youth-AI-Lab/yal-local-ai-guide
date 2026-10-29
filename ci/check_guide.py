"""Does what the guide asks in the browser (part 3 steps 6-7, parts 4 to 6), through the API of
Open WebUI, with the same settings, and checks what the guide says should happen.

Phases, run in this order between the stages of run_guide.py:
    admin         part 3, steps 6-7: the administrator account, the settings of openwebui.env
    chatbot       parts 4 and 5: knowledge, chatbot with Legacy and num_ctx 8192, an answer with sources
    participants  part 6, after the stage "network": safety net of the base model, Public access,
                  a participant account, what it sees and what the base model answers it
    journal       part 3, step 4: no e-mail and no address in the journal of the service (Linux),
                  or in ~/owui-local/open-webui.log, the log of owui-start.py (macOS, Windows)

Usage: python3 ci/check_guide.py <phase> [--os linux|macos|windows] (by default, the system it runs on)

Needs KIT_DIR (a copy of the workshop kit: its summaries are the documents) and OWUI_GUIDE_DIR (a
copy of the Open WebUI guide: its filled example of instructions). Only the standard library.
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
# The system of the guide's page that was followed (--os): by default, the one this runs on.
SYSTEM = {"darwin": "macos", "win32": "windows"}.get(sys.platform, "linux")

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

    def chat(self, model, question):
        # The page of Open WebUI loads the list of models first (a new chatbot is unknown until then),
        # and sends a session id: without it, Open WebUI never offers its own tools to the model.
        self.request("GET", "/api/models")
        # CI only: the tiny model of CI sometimes writes without end until its window is full (seen on
        # ubuntu-24.04: "slot context shift" in Ollama's journal, then a 15-minute timeout). A limit on
        # the length of this answer (max_tokens, num_predict for Ollama) changes no setting of the
        # chatbot: the checks read the sources and the tokens sent, not a long answer.
        return self.request("POST", "/api/chat/completions", body={
            "model": model, "stream": False, "session_id": "ci-" + uuid.uuid4().hex[:8],
            "max_tokens": 400, "messages": [{"role": "user", "content": question}]})

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

    print("Part 3, step 7: the connection to Ollama")
    models = [m["id"] for m in admin.request("GET", "/api/models")["data"]]
    check(MODEL in models, f"{MODEL} is in the list of models ({', '.join(models)})")
    data = admin.chat(MODEL, "Hello, who are you?")
    check(bool(answer_of(data).strip()), f"it answers: {answer_of(data)[:80]!r}")
    tokens = prompt_tokens(data)
    print(f"  info  the base model with the settings by default received {tokens} tokens")
    state["tokens_default"] = tokens


def phase_chatbot(state):
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


def phase_participants(state):
    if SYSTEM != "linux":
        wait_restarted()
    wait_ready()
    admin = Api(state["admin"])
    check(isinstance(admin.try_request("GET", "/auths/"), dict),
          "the restart of part 6, step 1, signs nobody out")
    print("Part 6, before the first session, step 3: the base model")
    got = admin.try_request("GET", "/models/model", query={"id": MODEL})
    base = None if isinstance(got, RuntimeError) else got  # no row yet: the model was never edited
    form = {"id": MODEL, "name": MODEL, "base_model_id": None, "is_active": True,
            "meta": {**((base or {}).get("meta") or {}), "capabilities": {
                **(((base or {}).get("meta") or {}).get("capabilities") or {}), "builtin_tools": False}},
            "params": {**((base or {}).get("params") or {}), "system": SAFETY, "function_calling": "legacy"}}
    admin.request("POST", "/models/model/update" if base else "/models/create", body=form)
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


def phase_journal(state):
    if SYSTEM == "linux":
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


def main():
    global SYSTEM
    phases = {"admin": phase_admin, "chatbot": phase_chatbot, "participants": phase_participants,
              "journal": phase_journal}
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=list(phases))
    parser.add_argument("--os", choices=["linux", "macos", "windows"], default=SYSTEM)
    args = parser.parse_args()
    SYSTEM, phase = args.os, args.phase
    wait_ready()
    state = load_state()
    phases[phase](state)
    save_state(state)
    if failures:
        sys.exit(f"{len(failures)} check(s) failed in phase {phase}")


if __name__ == "__main__":
    main()
