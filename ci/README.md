# The guide, followed by a machine

The workflow [`guide.yml`](../.github/workflows/guide.yml) follows this guide from start to end on
a fresh machine of GitHub, at each change and every Monday (the installers of Ollama and uv change
without us). The goal: each kind of computer the guide is written for can do it from start to end.

| System | Page | Machine of GitHub | State |
|---|---|---|---|
| Linux | [`linux.md`](../linux.md) | Ubuntu 26.04 (the system of the guide) and 24.04 | tested by the workflow |
| macOS | [`macos.md`](../macos.md) | macOS 26 on an Apple chip (`macos-26`) | tested by the workflow (first run: 29 October 2026) |
| Windows | [`windows.md`](../windows.md) | Windows Server 2025 (`windows-2025`) | tested by the workflow (first run: 29 October 2026); Windows 11 itself is not tested |
| Raspberry Pi | [`raspberry-pi.md`](../raspberry-pi.md) | Ubuntu 24.04 on an arm64 processor (`ubuntu-24.04-arm`) | tested by the workflow (first run: TO BE COMPLETED); Raspberry Pi OS itself is not tested |
| Raspberry Pi with the AI HAT+ 2 | [`raspberry-pi.md`](../raspberry-pi.md#with-the-ai-hat-2) | Ubuntu 24.04 on an arm64 processor (`ubuntu-24.04-arm`), with a stand-in for the AI HAT+ 2 ([below](#the-stand-in-for-the-ai-hat-2)) | tested by the workflow (first run: TO BE COMPLETED); Raspberry Pi OS and the AI HAT+ 2 themselves are not tested |

The machines of GitHub are not the reader's computer: no graphics card, no Windows 11 (Windows
Server instead), no Raspberry Pi and no AI HAT+ 2, and nobody in front of the screen to answer a
window that asks something.

## How it works

**The commands of the guide** run as they are written in the pages: first
[`README.md`](../README.md) (what every system shares), then the page of the system. A marker, an
HTML comment that GitHub does not show, says which code blocks to run, and what the reader should
see:

```html
<!-- ci linux stage=install check="uv --version" expect="uv 0.13.6" -->
```

- `linux`: the system this block is for (`linux`, `macos`, `windows`, `raspberry-pi`,
  `raspberry-pi-hat`, or several: `linux,macos`). `raspberry-pi` is the Raspberry Pi with the model
  on its processor (Ollama), and `raspberry-pi-hat` the same page with the AI HAT+ 2: both read
  `raspberry-pi.md`, and each runs only the blocks marked for it;
- `stage=`: [`run_guide.py`](run_guide.py) runs the blocks of one stage in order, in one shell, as
  in one window: `install` (parts 2 and 3; on the Raspberry Pi also step 1 of part 1, and with the
  AI HAT+ 2, its steps 3 to 7 instead of part 2), `network` (part 6, before the first session),
  `delete` (the deletion at the end of the project);
- `check="..."`: a command that the text asks the reader to type after the block;
- `expect="..."`: a text that the output must contain ("What you should see").

The shell is the reader's: bash on Linux and on the Raspberry Pi, zsh on macOS (the shell of the Terminal app), and Windows
PowerShell 5.1 on Windows (the one that comes with Windows, not PowerShell 7). On Windows:

- the blocks run under the policy of a new Windows 11 PC, which blocks every script file (`.ps1`).
  The machines of GitHub allow them all;
- each command of a block runs on its own, in the same window: `Set-Location`, `$env:` and the
  variables stay for the next block. The first error stops everything: a red error of PowerShell,
  or a program that ends with an exit code other than 0. A line that a program writes on its error
  output (uv and ollama write their progress there) is not an error;
- a new window takes the `PATH` of the settings of Windows, where the installers add their folder.
  Within one stage, the blocks run in the same window: a block must not ask the reader to open a
  new window to go on, but give the command that updates this one (as `export PATH=...` on Linux);
- a block must not use `break`, `continue` or `exit` outside a loop of its own.

Only these things change in the commands (`SUBSTITUTIONS` and `DOWNLOAD` in `run_guide.py`): the
machines of GitHub have no graphics card, so the model is `qwen2.5:0.5b` instead of `qwen2.5:7b`
(and instead of `qwen2.5:1.5b`, the model of the Raspberry Pi page);
on macOS, nobody can click **Open** in the window that asks whether to open Ollama, an app
downloaded from the internet, so `xattr` removes the mark that makes macOS ask (the reader clicks,
and this window is not tested); GitHub has no AI HAT+ 2, so in the job `raspberry-pi-hat` the
line `ExecStart=/usr/bin/hailo-ollama` of the service of hailo-ollama starts the stand-in instead
([below](#the-stand-in-for-the-ai-hat-2)); and a change tests its own `openwebui.env` and `owui-start.py` instead of the published ones. For
this, the guide downloads them exactly like this (`curl.exe` instead of `curl` in Windows
PowerShell):

```bash
curl -fsSLO https://raw.githubusercontent.com/Youth-AI-Lab/yal-local-ai-guide/main/openwebui.env
```

**What is done in the browser** (part 3 steps 6 and 7, parts 4 to 6) is done by
[`check_guide.py`](check_guide.py) through the programming interface of Open WebUI, with the same
settings as the guide: the administrator account, the settings of `openwebui.env`, a chatbot with
**Legacy** and **num_ctx 8192** on four summaries of the workshop kit, its sources, the safety net
of the base model, **Public** access, a participant account and what it sees, and no e-mail or
address in the journal (on Linux) or in `~/owui-local/open-webui.log`, the log that
[`owui-start.py`](../owui-start.py) writes (on macOS and Windows). With the AI HAT+ 2
(`--os raspberry-pi-hat`), it does steps 8 to 10 of the section of the HAT instead of part 4: the
connection to hailo-ollama, the model and a chatbot with **Legacy** and **Builtin Tools** off,
without documents. It first checks that with the settings by default Open WebUI sends its tools and
hailo-ollama refuses the question, then that no question carries tools once the settings are made,
that each fits in the 2,048 tokens of the HAT with an answer of 400 tokens, that the safety net
comes first, that hailo-ollama does not answer on the network address, and that no question reaches
its journal.

## The stand-in for the AI HAT+ 2

GitHub has no AI HAT+ 2, and the real `/usr/bin/hailo-ollama` needs Hailo's library and the chip.
The job `raspberry-pi-hat` still downloads, checks, installs and removes the real package of
hailo-ollama 5.1.1, with the commands of the page. Only the program that the service starts
changes: [`fake_hailo_ollama.py`](fake_hailo_ollama.py), a small Python program that runs no model.

**What it copies from hailo-ollama 5.1.1**, read in its code at the tag
[`v5.1.1`](https://github.com/hailo-ai/hailo_model_zoo_genai/tree/v5.1.1) (each behaviour names its
file and line): the same addresses (endpoints), JSON fields and status codes; the same settings file
and model folders, found the same way (the home folder first, unless `XDG_CONFIG_HOME` and
`XDG_DATA_HOME`, which the service of the page sets, say otherwise), so that the `sed` of the page
decides where it listens; the list of models of the
package; an error 500 "Node is NOT a STRING" when a question carries a list of `tools`, as oatpp, the
web library of hailo-ollama, answers; one question at a time; and each question written to its
standard output ("got prompt"), which the service of the page sends nowhere.

**What it adds of its own**: a fixed answer, or the text after "answer only:" in a first system
message (so that the safety net can be checked); a question of 2,048 tokens or more is refused with
an error 500 and noted (what hailo-ollama does then is not known); a small file instead of the
download of a model; and a log of the requests (`CI_HAILO_LOG`), one line per request, never the
text of a question. It counts tokens with the tokenizer of Qwen2, the file `tokenizer.json` of
`Qwen/Qwen2-1.5B-Instruct` at a fixed revision, checked by its fingerprint in `guide.yml`.
`--selftest` checks it before the guide runs.

**What it cannot show**: the speed, what really happens beyond 2,048 tokens, the chip, its driver,
the logs of Hailo's library, and the real program's reading of the requests. It is a copy, made
from the code, not hailo-ollama.

## When you change the guide

- **A command**: change it in the page; the workflow runs the new one. Keep the marker just before
  its code block.
- **A step in the browser** (parts 4 to 6): change `check_guide.py` too. It does not read the text of
  these parts.
- **A new block to run**: add a marker before it.
- **To see what will run**, without running it: `python3 ci/run_guide.py --os windows --stage install --print`.

## Test a change before it is published

This guide is written in a repository of the project that is not public, `yal-workshop` (folder
`guides/local-ai`), and published here at each push to its branch `main`; `guide.yml` then runs
here. To test a change first, its maintainers push it to a branch of `yal-workshop` whose name
starts with `local-ai/`, for example `local-ai/windows-page`: the workflow
`.github/workflows/local-ai-guide-test.yml` of `yal-workshop` runs the same jobs on it. They
can also start it by hand on any branch: **Actions** → **Local AI guide, on a branch** → **Run
workflow**. A change to a job of `guide.yml` goes in this copy too.

## What it does not check

The graphics card and its driver (part 1), the speed and the quality of the answers (a tiny model,
on a processor), the screens and their labels, the windows that ask the reader something (the
firewall of Windows or macOS, an administrator's confirmation), Windows 11 itself, Raspberry Pi
OS and its memory pages of 16 KB, the AI HAT+ 2 and its driver, and phones on a real Wi-Fi. Check these by hand on a real computer, as in the [About](../README.md#about) section.
