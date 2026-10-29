#!/usr/bin/env python3
# SPDX-License-Identifier: EUPL-1.2
"""A stand-in for hailo-ollama 5.1.1, for the CI of the Raspberry Pi page only.

This program is NOT hailo-ollama and runs no model. GitHub has no AI HAT+ 2, so the CI job
`raspberry-pi-hat` installs the real hailo-ollama 5.1.1 package, then starts this program in place
of `/usr/bin/hailo-ollama` (run_guide.py replaces the ExecStart line of the service). It answers
the HTTP API of hailo-ollama 5.1.1 as its source code does, so that Open WebUI 0.12.4 can be
checked against it:

- the same endpoints, the same JSON fields in the same order, the same status codes, the same
  settings file and the same model folders;
- an HTTP 500 "Node is NOT a STRING" when a request to /api/chat carries a list of "tools", as
  oatpp (the web library of hailo-ollama) answers;
- each prompt written to the standard output ("got prompt ..."), as 5.1.1 does: the service of the
  page sends that output nowhere (StandardOutput=null), and the CI checks the journal stays clean;
- one question at a time (one global lock), and a model that unloads after keep_alive.

What it adds of its own (CI only, not in hailo-ollama):

- the answer is a fixed sentence, or, when the first message is a system message that contains
  "answer only: TEXT", that TEXT (so that the safety net of the guide can be checked);
- a prompt of 2,048 tokens or more is refused with HTTP 500 and flagged in the log. What the real
  5.1.1 does then is not known (HailoRT only logs "Conversation context is full");
- a request log (--log, JSON Lines, one object per request, never the text of a message);
- "pulling" a model writes a small placeholder file instead of downloading the HEF file.

Each behaviour cites the file and line of the hailo-ollama source at tag v5.1.1 of
https://github.com/hailo-ai/hailo_model_zoo_genai (paths below are relative to that tag), or of
oatpp (https://github.com/oatpp/oatpp, commit 047b456, the last one before the 5.1.1 release;
hailo-ollama builds oatpp from its default branch, thirdparty/oatpp/CMakeLists.txt).

Usage:
    fake_hailo_ollama.py [--host H] [--port P] [--config FILE] [--data-dir DIR]
                         [--log FILE] (--tokenizer FILE | --approx-tokens)
                         [--context 2048] [--load-seconds 0] [--selftest]

Tokens are counted with the real Qwen2 tokenizer (--tokenizer, a tokenizer.json read with the
`tokenizers` package; the only import outside the standard library), or estimated (--approx-tokens:
one token per 3.5 bytes, which over-counts English text, measured at about 4 bytes per token).
--selftest starts the stand-in on 127.0.0.1:3998 with a temporary model folder and checks it.
"""

import argparse
import io
import itertools
import json
import math
import os
import re
import shutil
import signal
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERSION = "0.5.1"            # src/library/controller/controller.cpp 359-364
SERVER = "oatpp/1.4.0"       # strings of /usr/bin/hailo-ollama 5.1.1; oatpp Header::Value::SERVER
DEFAULT_KEEP_ALIVE = 300     # src/library/config/static_config.hpp: controller_default_keep_alive = 5 min
SHOW_PARAMETER_WIDTH = 30    # static_config.hpp: controller_show_parameter_width
PLACEHOLDER = "CI stand-in for hailo-ollama: not a HEF file\n"
DEFAULT_ANSWER = "This is the CI stand-in for hailo-ollama 5.1.1. It is not a model."
ANSWER_ONLY = re.compile(r"answer only:\s*(.+)$", re.IGNORECASE | re.MULTILINE)

# The chat template of qwen2:1.5b, copied from models/manifests/qwen2/1.5b/manifest.json at v5.1.1
# (identical in the .deb). It is the only template this stand-in renders (in plain Python, below).
QWEN2_TEMPLATE = (
    "{% for message in messages %}{% if loop.first and messages[0]['role'] != 'system' %}"
    "{{ '<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n' }}{% endif %}"
    "{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}"
    "{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}"
)
# The whole manifest of qwen2:1.5b, for --selftest. Copied from
# https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/models/manifests/qwen2/1.5b/manifest.json
QWEN2_MANIFEST = {
    "hef_h10h": "ab056548c60945cdf4fb30ca43fc7aeed2b9ffc751ad8d4c201dc4c4ab31e86a",
    "template_params": {"bos_token": "", "eos_token": "<|eot_id|>", "chat_template": QWEN2_TEMPLATE},
    "generation_params": {"stop_tokens": ["<|endoftext|>", "<|im_end|>"], "repetition_penalty": 1.1,
                          "temperature": 0.7, "top_p": 0.8, "top_k": 20},
    "license": None,
    "system_prompt": None,
    "details": {"parent_model": "", "format": "hef", "family": "qwen2", "families": ["qwen2"],
                "parameter_size": "1.5B", "quantization_level": "Q4_0"},
}

# ---------------------------------------------------------------------------------------------
# Request types, as declared in src/library/dto/DTOs.hpp (v5.1.1). "s" = String, "n" = a number
# or boolean field (Int32, UInt32, Float32, Int64, Int8, Boolean), ("obj", {...}) = Object<...>,
# ("vec", type) = Vector<...>. Fields that are not declared are ignored by oatpp
# (TreeToObjectMapper::Config allowUnknownFields = true).
MODEL_PARAMETERS = {"temperature": "n", "seed": "n", "top_k": "n", "top_p": "n",      # DTOs.hpp 21-33
                    "frequency_penalty": "n", "num_predict": "n", "use_mlock": "n"}
CHAT_MESSAGE = {"role": "s", "content": "s"}                                          # DTOs.hpp 50-55
CHAT_PARAMS = {"model": "s", "messages": ("vec", ("obj", CHAT_MESSAGE)),              # DTOs.hpp 57-69
               "tools": "s",  # line 63: DTO_FIELD(String, tools): a JSON list here is refused
               "format": "s", "options": ("obj", MODEL_PARAMETERS), "stream": "n", "keep_alive": "n"}
GENERATION_PARAMS = {"model": "s", "prompt": "s", "suffix": "s", "images": ("vec", "s"),  # 35-48
                     "format": "s", "options": ("obj", MODEL_PARAMETERS), "template": "s",
                     "stream": "n", "raw": "n", "keep_alive": "n"}
COMPLETION_PARAMS = {"model": "s", "messages": ("vec", ("obj", CHAT_MESSAGE)),        # DTOs.hpp 106-120
                     "frequency_penalty": "n", "presence_penalty": "n", "max_completion_tokens": "n",
                     "max_tokens": "n", "temperature": "n", "seed": "n", "top_p": "n",
                     "stream": "n", "n": "n"}
SHOW_PARAMS = {"model": "s"}                                                          # DTOs.hpp 175-179
PULL_PARAMS = {"model": "s", "stream": "n"}                                           # DTOs.hpp 194-199
DELETE_PARAMS = {"model": "s"}                                                        # DTOs.hpp 201-205

# Error texts of oatpp (commit 047b456).
NOT_A_STRING = "[oatpp::data::mapping::TreeToObjectMapper::mapString()]: Node is NOT a STRING"
NOT_PRIMITIVE = "[oatpp::data::mapping::TreeToObjectMapper::mapPrimitive()]: Value is NOT a Primitive type"
NOT_SUPPORTED = ("[oatpp::data::mapping::TreeChildrenOperator::TreeChildrenOperator()]: "
                 "Node type is NOT suppoerted")  # sic, Tree.cpp line 1005
NO_PAIRS = "[oatpp::data::mapping::TreeChildrenOperator::getPair()]: Node type doesn't support pairs"
NULL_POINTER = "[oatpp::data::type::String::operator std::string() const]: Error. Null pointer."
# What oatpp adds under the first line when an endpoint throws: ApiController.hpp 294-305
# ("[ApiController]: Error processing request") then HttpProcessor.cpp 117-118 ("Error processing
# request"), both with std::throw_with_nested. ErrorHandler.cpp (unwrapErrorStack) puts the innermost
# message first. The forum capture of thread 19327 (post 3) shows exactly these three lines.
WRAPPERS = ["[ApiController]: Error processing request", "Error processing request"]


def check_type(value, kind):
    """Return the error text oatpp gives when `value` does not fit `kind`, or None.

    oatpp's JSON mapper has allowLexicalCasting = false (TreeToObjectMapper.hpp, Config), and
    hailo-ollama does not change it (src/apps/server/app_component.hpp 318-331). So a String field
    accepts only a string or null (TreeToObjectMapper.cpp 180-271), and a number field only a
    number, a boolean or null (TreeToObjectMapper.hpp 78-115). The error that reaches the HTTP answer
    is the first one pushed (MappingError's what() is errorStack.front(), ObjectMapper.cpp 54-64),
    so only the innermost message is returned here.
    """
    if value is None:
        return None
    if kind == "s":
        return None if isinstance(value, str) else NOT_A_STRING
    if kind == "n":
        return None if isinstance(value, (int, float, bool)) else NOT_PRIMITIVE
    if kind[0] == "obj":
        if isinstance(value, list):
            # Approximation: the const getPair() on a vector; its text is assumed equal to the
            # non-const one (Tree.cpp 1026). Not seen in practice.
            return NO_PAIRS
        if not isinstance(value, dict):
            return NOT_SUPPORTED
        for key, item in value.items():  # oatpp walks the fields in the order of the JSON text
            if key in kind[1]:
                error = check_type(item, kind[1][key])
                if error:
                    return error
        return None
    if kind[0] == "vec":
        if isinstance(value, dict):
            # Approximation: oatpp would fail on getItem() of a map; its exact text is not checked.
            return NOT_SUPPORTED
        if not isinstance(value, list):
            return NOT_SUPPORTED
        for item in value:
            error = check_type(item, kind[1])
            if error:
                return error
        return None
    raise ValueError(kind)


# ---------------------------------------------------------------------------------------------
# Small helpers.

def iso_time(seconds_ns=None):
    """Time as hailo-ollama writes it: %FT%T, a dot, 9 digits, Z (src/library/utils/time.cpp 173-206)."""
    ns = time.time_ns() if seconds_ns is None else int(seconds_ns)
    whole, frac = divmod(ns, 1_000_000_000)
    return datetime.fromtimestamp(whole, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + f".{frac:09d}Z"


def dumps(obj):
    """JSON as oatpp writes it: compact, and no key whose value is null (app_component.hpp line 322:
    includeNullElements = false). Callers build dicts in the order of the DTO fields."""
    def strip(value):
        if isinstance(value, dict):
            return {k: strip(v) for k, v in value.items() if v is not None}
        if isinstance(value, list):
            return [strip(v) for v in value]
        return value
    return json.dumps(strip(obj), separators=(",", ":"), ensure_ascii=False)


class Out:
    """The standard output of the stand-in, as oatpp's DefaultLogger writes it (oatpp
    src/oatpp/Environment.cpp, DefaultLogger::log): every level goes to std::cout as
    "<colour> I <reset>|<local time %Y-%m-%d %H:%M:%S> <microseconds>| <tag>:<message>".
    --selftest swaps `stream` to read what was written."""
    lock = threading.Lock()
    stream = None

    @classmethod
    def info(cls, tag, message):
        now = time.time_ns()
        stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now // 1_000_000_000))
        line = f"\x1b[32m I \x1b[0m|{stamp} {now // 1000}| {tag}:{message}\n"
        with cls.lock:
            stream = cls.stream or sys.stdout
            stream.write(line)
            stream.flush()


def warn(message):
    """Errors of the stand-in go to the standard error, so they reach the journal. They never
    contain the text of a message or of a prompt."""
    sys.stderr.write(f"fake-hailo-ollama: {message}\n")
    sys.stderr.flush()


class TokenCounter:
    def __init__(self, tokenizer_file=None, approx=False):
        self.lock = threading.Lock()
        if tokenizer_file:
            from tokenizers import Tokenizer  # the only import outside the standard library
            self.tokenizer = Tokenizer.from_file(str(tokenizer_file))
            self.label = "qwen2-tokenizer"
        elif approx:
            self.tokenizer = None
            self.label = "approx"
        else:
            raise SystemExit("fake_hailo_ollama.py: choose how to count tokens: "
                             "--tokenizer FILE (exact, Qwen2) or --approx-tokens")

    def count(self, text):
        if self.tokenizer is None:
            return math.ceil(len(text.encode("utf-8")) / 3.5)
        with self.lock:
            # The special tokens of the template (<|im_start|>, <|im_end|>) are added tokens of
            # tokenizer.json and count one each. "Hello, who are you?" gives 25 tokens.
            return len(self.tokenizer.encode(text, add_special_tokens=False).ids)


# ---------------------------------------------------------------------------------------------
# Settings and model folders, found as hailo-ollama 5.1.1 finds them.

def find_dir(user_dir, other_dirs):
    """src/apps/server/main.cpp 47-65: the first existing `hailo-ollama` folder, in the user's
    folder first, then in each folder of the colon-separated list."""
    for option in [Path(user_dir)] + [Path(p) for p in other_dirs.split(":")]:
        candidate = option / "hailo-ollama"
        if candidate.is_dir():
            return candidate
    # The real program throws std::runtime_error("hailo-ollama directory not found") and stops.
    raise SystemExit("terminate called after throwing an instance of 'std::runtime_error'\n"
                     "  what():  hailo-ollama directory not found")


def xdg(name, home_suffix, default_dirs):
    """src/library/utils/path.cpp 217-251 and path.hpp 15-34."""
    home_var = os.environ.get(f"XDG_{name}_HOME") or ""
    user_dir = home_var or str(Path(os.environ.get("HOME", "")) / home_suffix)
    other_dirs = os.environ.get(f"XDG_{name}_DIRS") or default_dirs
    return user_dir, other_dirs


def config_file():
    return find_dir(*xdg("CONFIG", ".config", "/etc/xdg")) / "hailo-ollama.json"   # main.cpp 76


def data_dir():
    return find_dir(*xdg("DATA", ".local/share", "/usr/share:/usr/local/share"))   # main.cpp 95


class Store:
    """src/library/model/simple_store.cpp 128-169: every regular file under models/manifests is a
    manifest, named <parent of its folder>:<its folder>; names are kept sorted (std::map,
    simple_store.hpp line 24). Pulled models are files models/blob/sha256_<hef_h10h>
    (src/library/model/blob_resource.cpp 36-39)."""

    def __init__(self, data):
        models = Path(data) / "models"
        self.blob_dir = models / "blob"
        self.blob_dir.mkdir(exist_ok=True)              # main.cpp line 100: fs::create_directory
        self.models = {}
        manifests = models / "manifests"
        for path in sorted(p for p in manifests.rglob("*") if p.is_file()):
            name = f"{path.parent.parent.name}:{path.parent.name}"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            self.models[name] = {
                "hef": manifest["hef_h10h"],
                "template": manifest["template_params"]["chat_template"],
                "stop": (manifest.get("generation_params") or {}).get("stop_tokens", []),
                "details": manifest.get("details"),
            }
        self.models = dict(sorted(self.models.items()))

    def blob(self, name):
        return self.blob_dir / ("sha256_" + self.models[name]["hef"])

    def pulled(self, name):
        """controller.cpp 96-109 (get_model_data): known AND its HEF file exists."""
        return name in self.models and self.blob(name).is_file()

    def details(self, name):
        """ModelInfoDetails, DTOs.hpp 140-149 (field order; "format" defaults to "hef")."""
        d = self.models[name]["details"]
        if d is None:
            return None
        return {"parent_model": d.get("parent_model"), "format": d.get("format", "hef"),
                "family": d.get("family"), "families": d.get("families"),
                "parameter_size": d.get("parameter_size"),
                "quantization_level": d.get("quantization_level")}

    def info(self, name):
        """controller.cpp 111-141 (get_model_info) with ModelInfoShort, DTOs.hpp 151-161. There is
        no "digest": it is never set."""
        if not self.pulled(name):
            return None
        stat = self.blob(name).stat()
        return {"name": name, "model": name, "modified_at": iso_time(stat.st_mtime_ns),
                "size": stat.st_size, "details": self.details(name)}


# ---------------------------------------------------------------------------------------------
# The generation context: one model at a time, one request at a time.

class Context:
    """src/library/generation_context/generation_context.cpp and deconfigure.cpp: one global lock
    (SyncGenerationContext), the loaded model, its keep_alive, and the last prompt."""

    def __init__(self, load_seconds):
        self.lock = threading.Lock()
        self.load_seconds = load_seconds
        self.model = ""
        self.path = ""
        self.keep_alive = None          # seconds, or None for "never" (keep_alive < 0)
        self.last_use = 0.0
        self.last_prompt = ""
        self.stop = threading.Event()
        threading.Thread(target=self._deconfigure, daemon=True).start()

    def load(self, name, path, keep_alive):
        """generation_context.cpp 102-137 (load_model). The real one sleeps 2 s
        (generation_context_device_switch_sleep_time) and creates the LLM on the chip."""
        self.model = name
        self.last_use = time.monotonic()
        self.keep_alive = keep_alive
        if str(path) != self.path:
            self.path = str(path)
            if self.load_seconds:
                time.sleep(self.load_seconds)
            Out.info("GenerationThread", f"replacing model to {path}")
            self.last_prompt = ""

    def reset(self):
        """generation_context.cpp 192-199. last_prompt is not cleared here (as in 5.1.1); the next
        load clears it, because the path then differs."""
        Out.info("generation_context", "reset issued")
        self.model = ""
        self.path = ""
        self.keep_alive = None

    def expires(self):
        """generation_context.cpp 184-190: last use + keep_alive; None means never."""
        if self.keep_alive is None:
            return None
        return self.last_use + self.keep_alive

    def _deconfigure(self):
        """deconfigure.cpp 21-31: unload the model when keep_alive is over."""
        while not self.stop.wait(0.25):
            with self.lock:
                end = self.expires()
                if self.path and end is not None and time.monotonic() >= end:
                    self.reset()


def keep_alive_seconds(value):
    """controller.cpp 143-153 (convert_keep_alive): absent or null -> 5 minutes; < 0 -> never."""
    if value is None:
        return DEFAULT_KEEP_ALIVE
    value = int(value)
    return None if value < 0 else value


def render_qwen2(messages):
    """The qwen2:1.5b chat template (QWEN2_TEMPLATE), with add_generation_prompt = true, as
    controller.cpp 589-596 asks minja to render it."""
    out = []
    for i, message in enumerate(messages):
        if i == 0 and message.get("role") != "system":
            out.append("<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n")
        out.append("<|im_start|>" + message["role"] + "\n" + message["content"] + "<|im_end|>\n")
    out.append("<|im_start|>assistant\n")
    return "".join(out)


class Fail(Exception):
    """An error that oatpp turns into an HTTP answer with a text body (ErrorHandler.cpp 72-95)."""

    def __init__(self, message, code=500, wrapped=True):
        super().__init__(message)
        self.message = message
        self.code = code
        self.lines = [message] + (WRAPPERS if wrapped else [])


DESCRIPTIONS = {400: "Bad Request", 404: "Not Found", 500: "Internal Server Error"}


# ---------------------------------------------------------------------------------------------
# The HTTP server.

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    app = None   # set by make_server

    # Routes: src/library/controller/controller.hpp 53-98. There is no other endpoint.
    ROUTES = {
        ("GET", "/"): "root",
        ("GET", "/api/version"): "version",
        ("GET", "/api/tags"): "tags",
        ("GET", "/hailo/v1/list"): "list_all",
        ("GET", "/api/ps"): "ps",
        ("POST", "/api/show"): "show",
        ("POST", "/api/pull"): "pull",
        ("DELETE", "/api/delete"): "delete",
        ("POST", "/api/generate"): "generate",
        ("POST", "/api/chat"): "chat",
        ("POST", "/v1/chat/completions"): "completions",
    }

    def version_string(self):
        return SERVER

    def log_message(self, *args):
        pass   # no access log: hailo-ollama has none

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def do_DELETE(self):
        self.dispatch("DELETE")

    def do_PUT(self):
        self.dispatch("PUT")

    def do_HEAD(self):
        self.dispatch("HEAD")

    # -- plumbing ----------------------------------------------------------------------------

    def read_body(self):
        if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
            data = b""
            while True:
                size = int(self.rfile.readline().split(b";")[0].strip() or b"0", 16)
                if size == 0:
                    self.rfile.readline()
                    return data
                data += self.rfile.read(size)
                self.rfile.readline()
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def send(self, code, body=b"", content_type=None, close=False):
        self.send_response_only(code, DESCRIPTIONS.get(code) if code != 200 else "OK")
        self.send_header("Server", SERVER)
        if content_type:
            self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if close:
            self.send_header("Connection", "close")
            self.close_connection = True
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)
        self.wfile.flush()

    def send_json(self, obj, code=200):
        """createDtoResponse: Content-Type application/json."""
        self.send(code, dumps(obj).encode("utf-8"), "application/json")

    def send_error_text(self, fail):
        """oatpp ErrorHandler.cpp 72-95: a text body, headers Server and Connection: close."""
        body = (f"server={SERVER}\ncode={fail.code}\ndescription={DESCRIPTIONS[fail.code]}\n"
                "stacktrace:\n" + "".join(f"  - {line}\n" for line in fail.lines))
        self.send(fail.code, body.encode("utf-8"), close=True)

    def start_stream(self):
        """OutgoingStreamingBody: chunked, Content-Type application/x-ndjson (controller.cpp
        311-314 and 484-487)."""
        self.send_response_only(200, "OK")
        self.send_header("Server", SERVER)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

    def chunk(self, obj):
        """One object per line, each line ending in \\r\\n (llm_generation_callback.cpp 114-115 and
        136-137; pull_callback.cpp line 216)."""
        data = (dumps(obj) + "\r\n").encode("utf-8")
        self.wfile.write(f"{len(data):x}\r\n".encode() + data + b"\r\n")
        self.wfile.flush()

    def end_stream(self):
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()

    def dispatch(self, method):
        app = self.app
        path = self.path.split("?", 1)[0]
        record = {"seq": None, "time": iso_time(), "method": method, "path": path, "status": None,
                  "model": None, "stream": None, "top_keys": [], "options_keys": [],
                  "has_tools": False, "tools_type": None, "messages": None, "roles": [],
                  "system_first": False, "prompt_tokens": None, "token_count": None,
                  "num_predict": None, "over_context": False, "continuation": False,
                  "eval_count": None, "error": None}
        self.record = record
        self.logged = False
        try:
            body = self.read_body() if method in ("POST", "PUT", "DELETE") else b""
            name = self.ROUTES.get((method, path))
            if name is None:
                # oatpp HttpProcessor.cpp 105-110: HttpError 404, wrapped once (line 117-118).
                raise Fail(f"No mapping for HTTP-method: '{method}', URL: '{path}'", 404, wrapped=False) \
                    from None
            if method == "GET":
                getattr(self, "do_" + name)()
            else:
                params = self.parse(body, name)
                getattr(self, "do_" + name)(params)
        except Fail as fail:
            record["status"] = fail.code
            record["error"] = fail.message
            if fail.code == 404:
                fail.lines = [fail.message, "Error processing request"]
            else:
                warn(f"HTTP {fail.code} on {method} {path}: {fail.message}")
            self.log()
            self.send_error_text(fail)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
            self.log()

    def parse(self, body, name):
        """BODY_DTO (oatpp codegen/api_controller/base_define.hpp 237-246): read the JSON into the
        DTO, then refuse a null body with HTTP 400."""
        schema, param = {
            "show": (SHOW_PARAMS, "show_params"), "pull": (PULL_PARAMS, "pull_params"),
            "delete": (DELETE_PARAMS, "delete_params"), "generate": (GENERATION_PARAMS, "generation_params"),
            "chat": (CHAT_PARAMS, "generation_params"),
            "completions": (COMPLETION_PARAMS, "generation_params"),
        }[name]
        try:
            params = json.loads(body.decode("utf-8")) if body.strip() else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            # Approximation: the text of oatpp's JSON parser error is not copied.
            raise Fail("fake-hailo-ollama: the body is not valid JSON "
                       "(the real error text of oatpp is not copied)") from None
        record = self.record
        if isinstance(params, dict):
            record["top_keys"] = sorted(params)
            record["model"] = params.get("model") if isinstance(params.get("model"), str) else None
            options = params.get("options")
            record["options_keys"] = sorted(options) if isinstance(options, dict) else []
            tools = params.get("tools")
            record["has_tools"] = "tools" in params and tools is not None
            record["tools_type"] = (None if tools is None else "list" if isinstance(tools, list)
                                    else "dict" if isinstance(tools, dict) else "str")
            num_predict = options.get("num_predict") if isinstance(options, dict) else None
            record["num_predict"] = int(num_predict) if isinstance(num_predict, (int, float)) else None
            if isinstance(params.get("stream"), bool):
                record["stream"] = params["stream"]
            messages = params.get("messages")
            if isinstance(messages, list):
                record["messages"] = len(messages)
                record["roles"] = [m.get("role") if isinstance(m, dict) else None for m in messages]
                record["system_first"] = bool(record["roles"]) and record["roles"][0] == "system"
        if params is None:
            raise Fail(f"Missing valid body parameter '{param}'", 400)
        error = check_type(params, ("obj", schema))
        if error:
            raise Fail(error)
        return params

    def log(self, **fields):
        """One JSON line per request (--log). Written before the last bytes of the answer leave,
        so that a client that has its answer always finds the line."""
        if self.logged:
            return
        self.logged = True
        self.record.update(fields)
        self.app.write_log(self.record)

    @staticmethod
    def model_name(params):
        """Using a null "model" converts a null oatpp::String to std::string: oatpp throws
        "Error. Null pointer." (seen on the forum, thread 19327 post 7, for /api/show)."""
        model = params.get("model")
        if model is None:
            raise Fail(NULL_POINTER)
        return model

    # -- endpoints ---------------------------------------------------------------------------

    def do_root(self):
        """controller.cpp 352-357."""
        self.record["status"] = 200
        self.log()
        self.send(200, b"hailo-ollama is running", "text/plain")

    def do_version(self):
        """controller.cpp 359-364."""
        self.record["status"] = 200
        self.log()
        self.send_json({"version": VERSION})

    def do_tags(self):
        """controller.cpp 366-380: only the models already pulled."""
        store = self.app.store
        Out.info("list_models", f"got {len(store.models)} models in store")
        models = []
        for name in store.models:
            Out.info("list_models", f"model: {name}")
            info = store.info(name)
            if info:
                models.append(info)
        self.record["status"] = 200
        self.log()
        self.send_json({"models": models})

    def do_list_all(self):
        """controller.cpp 382-392: every manifest name, pulled or not, sorted."""
        Out.info("list_models", f"got {len(self.app.store.models)} models in store")
        self.record["status"] = 200
        self.log()
        self.send_json({"models": list(self.app.store.models)})

    def do_ps(self):
        """controller.cpp 394-409: takes the generation lock, then lists the loaded model."""
        ctx = self.app.ctx
        with ctx.lock:
            name, end = ctx.model, ctx.expires()
        models = []
        info = self.app.store.info(name) if name else None
        if info:
            if end is None:
                # The real value is steady_clock::time_point::max() converted to system time,
                # which overflows (time.cpp 213-225): not copied. A far date stands in for it.
                info["expires_at"] = "2262-04-11T23:47:16.854775807Z"
            else:
                info["expires_at"] = iso_time(time.time_ns() + (end - time.monotonic()) * 1e9)
            models.append(info)
        self.record["status"] = 200
        self.log()
        self.send_json({"models": models})

    def do_show(self, params):
        """controller.cpp 411-451, ShowResponse DTOs.hpp 181-192. A model that is not pulled gives
        HTTP 200 with an error. "model_info" is the empty string, not an object; "license" is the
        empty string (ModelInfo.license is never filled, simple_store.cpp 109-126); no
        "capabilities"."""
        store = self.app.store
        name = self.model_name(params)
        self.record["status"] = 200
        if not store.pulled(name):
            self.record["error"] = f"model '{name}' not found"
            self.log()
            self.send_json({"error": f"model '{name}' not found"})
            return
        model = store.models[name]
        parameters = "\n".join("stop" + '"'.rjust(SHOW_PARAMETER_WIDTH) + tok + '"' for tok in model["stop"])
        self.log()
        self.send_json({"license": "", "modelfile": "", "parameters": parameters,
                        "template": model["template"], "details": store.details(name),
                        "model_info": "", "modified_at": store.info(name)["modified_at"]})

    def do_pull(self, params):
        """controller.cpp 453-488, blob_resource.cpp 118-149, writefile_callback.cpp 266-286.
        No download: a placeholder file stands for the HEF file. The real program also checks the
        SHA-256 of a file already there and downloads it again if it differs; the placeholder can
        never match, so here a file that exists counts as pulled."""
        store = self.app.store
        name = self.model_name(params)
        self.record["status"] = 200
        if name not in store.models:
            self.record["error"] = f"model '{name}' not found"
            self.log()
            self.send_json({"error": f"model '{name}' not found"})
            return
        already = store.pulled(name)
        if not already:
            tmp = store.blob(name).with_name(store.blob(name).name + ".tmp")
            tmp.write_text(PLACEHOLDER)
            tmp.rename(store.blob(name))
        stream = params.get("stream", True)
        if not stream:
            self.log()
            self.send_json({"status": "success"})
            return
        self.start_stream()
        if not already:
            total = len(PLACEHOLDER)
            digest = store.models[name]["hef"]
            for completed in (total // 3, 2 * total // 3, total):
                self.chunk({"status": "pulling", "digest": digest, "total": total, "completed": completed})
            self.chunk({"status": "verifying sha256 digest"})
        self.log()
        self.chunk({"status": "success"})
        self.end_stream()

    def do_delete(self, params):
        """controller.cpp 490-511: HTTP 404 with a JSON error, or HTTP 200 with an empty body."""
        store = self.app.store
        name = self.model_name(params)
        if not store.pulled(name):
            self.record.update(status=404, error="model not found")
            self.log()
            self.send_json({"code": "not_found", "error": "model not found"}, 404)
            return
        store.blob(name).unlink()
        self.record["status"] = 200
        self.log()
        self.send(200)

    def do_generate(self, params):
        """controller.cpp 513-559: as chat, with one user message made from "prompt"."""
        name = self.model_name(params)
        if not self.app.store.pulled(name):
            return self.not_found(name)
        if params.get("prompt") is None:
            return self.load_unload(name, params, as_message=False)
        messages = [{"role": "user", "content": params["prompt"]}]
        self.record.update(messages=1, roles=["user"], system_first=False)
        self.complete(name, messages, params, "response")

    def do_chat(self, params):
        """controller.cpp 561-607."""
        name = self.model_name(params)
        if not self.app.store.pulled(name):
            return self.not_found(name)
        if params.get("messages") is None:
            return self.load_unload(name, params, as_message=True)
        self.complete(name, params["messages"], params, "message")

    def do_completions(self, params):
        """controller.cpp 609-675. Only non-streamed answers. "tools" is not a field of
        CreateChatCompletionParams, so here it is ignored, not refused."""
        def soft_error(text):
            self.record.update(status=200, error=text)
            self.log()
            self.send_json({"error": text})
        if params.get("messages") is None:
            return soft_error("messages field is required")
        if params.get("n", 1) != 1:          # Int8 n = 1 by default; an explicit null is not 1
            return soft_error("only n == 1 is supported")
        if params.get("stream", False):
            return soft_error("streaming not supported on this endpoint. Use /api/chat endpoint instead.")
        name = self.model_name(params)
        if not self.app.store.pulled(name):
            return self.not_found(name)
        options = {}
        for key in ("temperature", "seed", "top_p", "frequency_penalty"):
            options[key] = params.get(key)
        if params.get("max_tokens"):
            options["num_predict"] = params["max_tokens"]
        if params.get("max_completion_tokens"):
            options["num_predict"] = params["max_completion_tokens"]
        self.record["num_predict"] = int(options["num_predict"]) if "num_predict" in options else None
        self.complete(name, params["messages"], {"options": options, "stream": False}, "completion")

    def not_found(self, name):
        """controller.cpp 518-523, 564-569, 629-634: HTTP 200 with an error."""
        text = f"model '{name}' not found"
        self.record.update(status=200, error=text)
        self.log()
        self.send_json({"error": text})

    def load_unload(self, name, params, as_message):
        """controller.cpp 317-350: no messages (or no prompt) loads the model; keep_alive 0
        unloads it. GenerationResponseFinal field order, DTOs.hpp 81-97."""
        ctx = self.app.ctx
        keep_alive = params.get("keep_alive")
        with ctx.lock:
            if keep_alive is not None and int(keep_alive) == 0:
                ctx.reset()
                reason = "unload"
            else:
                ctx.load(name, self.app.store.blob(name), keep_alive_seconds(keep_alive))
                reason = "load"
        result = {"model": name, "created_at": iso_time()}
        if as_message:
            result["message"] = {"role": "assistant", "content": ""}
        else:
            result["response"] = ""
        result.update(done=True, done_reason=reason)
        self.record["status"] = 200
        self.log()
        self.send_json(result)

    def complete(self, name, messages, params, kind):
        """controller.cpp 155-315 (handle_completion) and generation_context.cpp 139-174."""
        app, ctx, store = self.app, self.app.ctx, self.app.store
        model = store.models[name]
        if model["template"] != QWEN2_TEMPLATE:
            raise Fail("fake-hailo-ollama: only the template of qwen2:1.5b is implemented")
        if any(m.get("role") is None or m.get("content") is None for m in messages):
            # Approximation: minja's error on a null role or content is not copied.
            raise Fail("fake-hailo-ollama: a message without role or content "
                       "(the real error of minja is not copied)")
        prompt = render_qwen2(messages)
        options = params.get("options") or {}
        num_predict = options.get("num_predict")
        num_predict = None if num_predict is None else int(num_predict)
        stream = params.get("stream", True) if kind != "completion" else False
        if stream is None:
            stream = False   # Approximation: an explicit null "stream"; oatpp's bool of null not checked
        stream = bool(stream)
        self.record["stream"] = stream
        begin = time.monotonic_ns()
        with ctx.lock:   # SyncGenerationContext: one generation at a time (controller.cpp line 186)
            Out.info("handle_completion", f"Got model {store.blob(name)}")
            # generation_context.cpp line 141: the whole rendered prompt goes to the standard output.
            Out.info("GenerationThread", f"got prompt {prompt}")
            keep_alive = None if kind == "completion" else params.get("keep_alive")
            ctx.load(name, store.blob(name), keep_alive_seconds(keep_alive))
            tokens = app.counter.count(prompt)
            # generation_context.cpp 146-156: the new prompt continues the last one, or the
            # context is cleared and the whole prompt is written.
            continuation = bool(ctx.last_prompt) and prompt.startswith(ctx.last_prompt) \
                and len(prompt) != len(ctx.last_prompt)
            ctx.last_prompt = prompt
            self.record.update(prompt_tokens=tokens, token_count=app.counter.label,
                               num_predict=num_predict, continuation=continuation)
            if tokens >= app.context:
                # The stand-in's own rule (CI only). What 5.1.1 does with a prompt that does not
                # fit is not known: HailoRT only logs "Conversation context is full".
                self.record["over_context"] = True
                raise Fail(f"fake-hailo-ollama (CI only): a prompt of {tokens} tokens does not fit "
                           f"in the {app.context}-token context")

            answer = DEFAULT_ANSWER
            if messages and messages[0].get("role") == "system":
                found = ANSWER_ONLY.findall(messages[0]["content"])
                if found:
                    answer = found[-1].strip()
            words = answer.split(" ")
            reason = "stop"
            if num_predict is not None and num_predict < len(words):
                words, reason = words[:num_predict], "length"
            text = " ".join(words)
            # What 5.1.1 appends to its last prompt: in a streamed answer the text then the stop
            # token (llm_generation_callback.cpp 55, 64-87); in a non-streamed answer the stop
            # token first, then the text (controller.cpp 223 then 288). Tokens HailoRT may write
            # after the stop token are not known and not added.
            stop_token = "<|im_end|>" if reason == "stop" else ""
            ctx.last_prompt += (text + stop_token) if stream else (stop_token + text)

            if kind == "completion":
                self.record.update(status=200, eval_count=len(words))
                self.log()
                self.send_json({"id": f"chatcmpl-{next(app.ids)}", "object": "chat.completion",
                                "created": time.time_ns(),   # system_clock count: nanoseconds
                                "model": name,
                                "choices": [{"index": 0, "message": {"role": "assistant", "content": text},
                                             "finish_reason": reason}]})
                return
            if not stream:
                result = {"model": name, "created_at": iso_time()}
                result[kind] = {"role": "assistant", "content": text} if kind == "message" else text
                result.update(done=True, done_reason=reason,
                              total_duration=time.monotonic_ns() - begin, eval_count=len(words))
                self.record.update(status=200, eval_count=len(words))
                self.log()
                self.send_json(result)
                return
            # Streamed: one line per word ("token"), then a final line with empty content
            # (llm_generation_callback.cpp 46-143; GenerationResponse DTOs.hpp 71-79).
            self.start_stream()
            for i, word in enumerate(words):
                piece = word + (" " if i < len(words) - 1 else "")
                line = {"model": name, "created_at": iso_time()}
                line[kind] = {"role": "assistant", "content": piece} if kind == "message" else piece
                line["done"] = False
                self.chunk(line)
            final = {"model": name, "created_at": iso_time()}
            final[kind] = {"role": "assistant", "content": ""} if kind == "message" else ""
            final.update(done=True, done_reason=reason, total_duration=time.monotonic_ns() - begin,
                         eval_count=len(words))
            self.record.update(status=200, eval_count=len(words))
            self.log()
            self.chunk(final)
            self.end_stream()


class App:
    def __init__(self, store, counter, context, load_seconds, log_path):
        self.store = store
        self.counter = counter
        self.context = context
        self.ctx = Context(load_seconds)
        self.ids = itertools.count(1)   # 5.1.1 uses std::rand() (controller.cpp line 258)
        self.log_lock = threading.Lock()
        self.seq = itertools.count(1)
        self.log_file = open(log_path, "a", encoding="utf-8") if log_path else None

    def write_log(self, record):
        if not self.log_file:
            return
        with self.log_lock:
            record["seq"] = next(self.seq)
            self.log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            self.log_file.flush()


def make_server(host, port, app):
    handler = type("BoundHandler", (Handler,), {"app": app})
    server = ThreadingHTTPServer((host, port), handler)   # AF_INET: IPv4 only (app_component.hpp line 30)
    server.daemon_threads = True
    return server


# ---------------------------------------------------------------------------------------------
# --selftest

def selftest(args, counter):
    tmp = Path(tempfile.mkdtemp(prefix="fake-hailo-ollama-"))
    failures = []

    def check(ok, label):
        print(("ok   " if ok else "FAIL ") + label, flush=True)
        if not ok:
            failures.append(label)

    try:
        manifest = tmp / "share" / "hailo-ollama" / "models" / "manifests" / "qwen2" / "1.5b"
        manifest.mkdir(parents=True)
        (manifest / "manifest.json").write_text(json.dumps(QWEN2_MANIFEST, indent=4), encoding="utf-8")
        port = args.port or 3998
        log_path = Path(args.log) if args.log else tmp / "requests.jsonl"
        app = App(Store(tmp / "share" / "hailo-ollama"), counter, args.context, args.load_seconds, log_path)
        server = make_server("127.0.0.1", port, app)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{port}"

        def call(path, body=None, method=None):
            data = None if body is None else json.dumps(body).encode()
            req = urllib.request.Request(base + path, data=data, method=method,
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return resp.status, resp.read().decode("utf-8"), dict(resp.headers)
            except urllib.error.HTTPError as err:
                return err.code, err.read().decode("utf-8"), dict(err.headers)

        def last_log():
            return json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])

        hello = [{"role": "user", "content": "Hello, who are you?"}]
        Out.stream = io.StringIO()   # the server's own output (prompts included) stays out of the CI log

        status, body, _ = call("/")
        check(status == 200 and body == "hailo-ollama is running", "1. GET / says hailo-ollama is running")
        status, body, _ = call("/api/version")
        check(status == 200 and json.loads(body) == {"version": VERSION}, "1. /api/version gives 0.5.1")

        status, body, _ = call("/api/tags")
        check(status == 200 and json.loads(body) == {"models": []}, "2. /api/tags is empty before the pull")
        status, body, _ = call("/hailo/v1/list")
        check(status == 200 and "qwen2:1.5b" in json.loads(body)["models"], "2. /hailo/v1/list has qwen2:1.5b")

        status, body, headers = call("/api/pull", {"model": "qwen2:1.5b", "stream": True})
        lines = [json.loads(x) for x in body.splitlines() if x.strip()]
        check(status == 200 and headers.get("Content-Type") == "application/x-ndjson"
              and lines[-1] == {"status": "success"} and lines[0]["status"] == "pulling",
              "3. streamed /api/pull ends with success")
        status, body, _ = call("/api/tags")
        models = json.loads(body)["models"]
        check(len(models) == 1 and models[0]["name"] == "qwen2:1.5b"
              and models[0]["details"]["format"] == "hef" and "digest" not in models[0],
              "3. /api/tags lists qwen2:1.5b, format hef, no digest")

        status, body, headers = call("/api/chat", {"model": "qwen2:1.5b", "messages": hello,
                                                   "tools": [], "stream": False})
        check(status == 500 and "Node is NOT a STRING" in body and headers.get("Connection") == "close"
              and last_log()["has_tools"] and last_log()["status"] == 500,
              '4. /api/chat with "tools": [] gives HTTP 500 Node is NOT a STRING')

        captured = io.StringIO()
        Out.stream = captured
        status, body, _ = call("/api/chat", {"model": "qwen2:1.5b", "messages": hello, "stream": False})
        Out.stream = io.StringIO()
        answer = json.loads(body)
        entry = last_log()
        check(status == 200 and answer.get("done") is True and "prompt_eval_count" not in answer
              and answer["message"]["content"] == DEFAULT_ANSWER, "5. non-streamed /api/chat: done, no prompt_eval_count")
        if counter.tokenizer is not None:
            check(entry["prompt_tokens"] == 25 and entry["token_count"] == "qwen2-tokenizer",
                  "5. 'Hello, who are you?' counts 25 tokens with the Qwen2 tokenizer")
        else:
            print(f"skip 5. exact count (approx: {entry['prompt_tokens']} tokens)", flush=True)
        check("Hello, who are you?" not in log_path.read_text(encoding="utf-8"),
              "5. the log never holds the text of a message")
        check("GenerationThread:got prompt <|im_start|>system" in captured.getvalue(),
              "9. the prompt goes to the standard output (got prompt)")

        status, body, headers = call("/api/chat", {"model": "qwen2:1.5b", "messages": hello})
        raw = body.split("\n")[:-1]
        check(status == 200 and headers.get("Transfer-Encoding") == "chunked"
              and all(x.endswith("\r") for x in raw) and json.loads(raw[-1])["done"] is True
              and "".join(json.loads(x)["message"]["content"] for x in raw) == DEFAULT_ANSWER,
              "6. streamed /api/chat: every line ends in \\r\\n, the last has done:true")

        long = [{"role": "user", "content": "forest fire " * 2000}]
        status, body, _ = call("/api/chat", {"model": "qwen2:1.5b", "messages": long, "stream": False})
        check(status == 500 and last_log()["over_context"] is True and "does not fit" in body,
              "7. a prompt over 2,048 tokens gives HTTP 500 and over_context")

        safety = [{"role": "system", "content": "You are not the group's chatbot. To any question, "
                   "answer only: please choose the group's chatbot in the list."},
                  {"role": "user", "content": "Hello"}]
        status, body, _ = call("/api/chat", {"model": "qwen2:1.5b", "messages": safety, "stream": False})
        check(status == 200 and json.loads(body)["message"]["content"]
              == "please choose the group's chatbot in the list." and last_log()["system_first"],
              "8. 'answer only:' gives exactly that answer")

        status, body, _ = call("/v1/chat/completions", {"model": "qwen2:1.5b", "messages": hello, "stream": True})
        check(status == 200 and "streaming not supported" in json.loads(body)["error"],
              "10. /v1/chat/completions with stream:true gives 200 and the error")

        status, body, _ = call("/api/show", {"name": "qwen2:1.5b"})
        check(status == 500 and "Null pointer" in body, '11. /api/show with "name" only gives HTTP 500')
        status, body, _ = call("/api/show", {"model": "qwen2:1.5b", "name": "qwen2:1.5b"})
        show = json.loads(body) if status == 200 else {}
        check(status == 200 and show.get("model_info") == "" and "capabilities" not in show
              and show.get("parameters", "").startswith("stop" + " " * 29 + '"<|endoftext|>"'),
              '11. /api/show with "model" gives 200 and model_info ""')

        # Extra checks (not in the spec's list): load state, unload, delete, unknown routes.
        status, body, _ = call("/api/ps")
        check([m["name"] for m in json.loads(body)["models"]] == ["qwen2:1.5b"], "+ /api/ps lists the loaded model")
        status, body, _ = call("/api/generate", {"model": "qwen2:1.5b", "keep_alive": 0})
        check(json.loads(body).get("done_reason") == "unload", "+ keep_alive 0 unloads the model")
        status, body, _ = call("/api/ps")
        check(json.loads(body) == {"models": []}, "+ /api/ps is empty after the unload")
        status, body, _ = call("/api/chat", {"model": "nope:1b", "messages": hello})
        check(status == 200 and json.loads(body) == {"error": "model 'nope:1b' not found"},
              "+ an unknown model gives HTTP 200 with an error")
        status, body, _ = call("/api/chat", {"model": "qwen2:1.5b", "messages": hello, "keep_alive": "5m"})
        check(status == 500 and "NOT a Primitive" in body, '+ keep_alive "5m" gives HTTP 500')
        status, body, _ = call("/api/delete", {"model": "qwen2:1.5b"}, method="DELETE")
        check(status == 200 and body == "", "+ /api/delete gives 200 and an empty body")
        status, body, _ = call("/api/delete", {"model": "qwen2:1.5b"}, method="DELETE")
        check(status == 404 and json.loads(body) == {"code": "not_found", "error": "model not found"},
              "+ a second /api/delete gives 404")
        status, body, _ = call("/api/embed", {"model": "qwen2:1.5b"})
        check(status == 404, "+ /api/embed does not exist (404)")

        server.shutdown()
        server.server_close()
    finally:
        Out.stream = None
        shutil.rmtree(tmp, ignore_errors=True)
    print("FAILED: " + str(len(failures)) if failures else "All checks passed.", flush=True)
    return 1 if failures else 0


# ---------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--host", help="address to listen on (default: server.host of the settings file)")
    parser.add_argument("--port", type=int, help="port (default: server.port of the settings file)")
    parser.add_argument("--config", help="the settings file (default: found as hailo-ollama 5.1.1 finds it)")
    parser.add_argument("--data-dir", help="the folder that holds models/ (default: as hailo-ollama 5.1.1)")
    parser.add_argument("--log", help="append one JSON line per request to this file")
    count = parser.add_mutually_exclusive_group()
    count.add_argument("--tokenizer", help="tokenizer.json of Qwen2, for exact token counts")
    count.add_argument("--approx-tokens", action="store_true", help="estimate: 1 token per 3.5 bytes")
    parser.add_argument("--context", type=int, default=2048, help="context size in tokens (default 2048)")
    parser.add_argument("--load-seconds", type=float, default=0.0, help="time to load a model (default 0)")
    parser.add_argument("--selftest", action="store_true", help="check the stand-in on 127.0.0.1:3998")
    args = parser.parse_args()

    counter = TokenCounter(args.tokenizer, args.approx_tokens)
    if args.selftest:
        sys.exit(selftest(args, counter))

    settings = json.loads(Path(args.config or config_file()).read_text(encoding="utf-8"))
    host = args.host or settings["server"]["host"]
    port = args.port or int(settings["server"]["port"])
    store = Store(args.data_dir or data_dir())
    app = App(store, counter, args.context, args.load_seconds, args.log)
    server = make_server(host, port, app)

    def stop(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    Out.info("MyApp", f"Server running on port {port}")          # main.cpp 131-135
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        Out.info("MyApp", "Stop signal received, please wait for server shutdown")   # main.cpp 147-150
    finally:
        app.ctx.stop.set()
        server.server_close()


if __name__ == "__main__":
    main()
