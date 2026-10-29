# Raspberry Pi: install the chatbot on a Raspberry Pi 5

This page is part of the guide [A chatbot that runs on your own computer](README.md). It holds what
depends on the system of the computer, here a **Raspberry Pi 5 with 8 GB of memory**, under
**Raspberry Pi OS Trixie, 64 bits**: parts 1 to 3, the commands of part 6, the deletion at the end
of the project, and the commands and troubleshooting of the Raspberry Pi. It adds an optional
section, [With the AI HAT+ 2](#with-the-ai-hat-2), for an extra AI board of the Pi.

Do parts 1 to 3 on this page. Then go back to the guide for
[part 4](README.md#part-4---build-the-chatbot), [part 5](README.md#part-5---test-it) and
[part 6](README.md#part-6---open-it-to-your-group). When part 6 needs a command, it sends you back
to this page. The words *terminal*, `sudo`, *driver*, *service* and *port* are explained in the
[prerequisites](README.md#prerequisites) of the guide. If you have the AI HAT+ 2, do also the
section [With the AI HAT+ 2](#with-the-ai-hat-2) after part 3.

Another system: [Linux](linux.md), [macOS](macos.md), [Windows](windows.md).

> [!WARNING]
> **A technical part.** Parts 1 to 3 use commands typed in a terminal, some with the administrator
> rights of the computer (`sudo`), and they change its settings. Do them only if you feel confident
> with this.

> [!NOTE]
> **Not tested on a real Raspberry Pi.** We measured the guide on Linux only. The commands of this
> page come from the documentation of Raspberry Pi, Hailo, Ollama and uv, and from the code of
> hailo-ollama 5.1.1. A machine of GitHub with an arm64 processor, under Ubuntu 24.04 (not
> Raspberry Pi OS), is set to follow step 1 of part 1, parts 2 and 3, parts 4 to 6 (the steps in
> the browser through Open WebUI's programming interface) and the deletion. For the AI HAT+ 2, it
> follows steps 3 to 10 of [With the AI HAT+ 2](#with-the-ai-hat-2) instead of part 2, with a small
> program that answers like hailo-ollama 5.1.1 in place of hailo-ollama and the HAT
> ([`ci/README.md`](ci/README.md)). Date of its first successful run: TO BE COMPLETED. TO BE
> COMPLETED: a run on a real Raspberry Pi 5, with and without the AI HAT+ 2, and a group.

**Two ways to run the model.** By default, the model runs on the **processor** of the Pi, with
Ollama, as on the other pages: parts 1 to 6 of the guide stay the same. The **AI HAT+ 2** is an
extra board for the Pi 5, with its own AI chip and its own memory. With it, a program of Hailo, the
maker of the chip, runs the model on the HAT: **hailo-ollama**. Its models hold only **2,048
tokens** at a time
([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/docs/MODELS.rst),
[HailoRT](https://github.com/hailo-ai/hailort/blob/v5.1.1/hailort/libhailort/include/hailo/genai/llm/llm.hpp)).
A *token* is a small piece of a word. These 2,048 tokens are the model's memory for one answer (its
*context window*): your instructions, the conversation and the answer must all fit in it. That is
enough for a chatbot **without documents** and short conversations, not for the chatbot
with documents of part 4. See [With the AI HAT+ 2](#with-the-ai-hat-2).

**The terminal** is the app where you type commands. Raspberry Pi's documentation says "open the
Raspberry Pi Terminal" ([Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html)).
Its place in the menu of the Pi: TO BE COMPLETED. When a command starts with `sudo`, the terminal
asks for the password of your account on the Pi.

---

## Part 1 - Check the computer

This part checks that the computer is a Raspberry Pi 5 under the 64-bit Raspberry Pi OS Trixie,
that it is up to date, and that it has enough power, cooling and space. A Raspberry Pi has no
graphics card that Ollama can use ([part 2](#part-2---install-ollama-and-a-model)): the model runs
on its processor, or on the AI HAT+ 2.
Do this part before part 2.

### Step 1 - Check the board and its system

Open a terminal and type:

<!-- ci raspberry-pi,raspberry-pi-hat stage=install expect="arm64" -->
```bash
dpkg --print-architecture
grep VERSION_CODENAME /etc/os-release
free -h
```

The first command shows for which kind of processor the system is made. The second one shows the
name of its version. The third one shows the memory of the computer.

**What you should see.** Three answers:

- `arm64`: a 64-bit system;
- `VERSION_CODENAME=trixie`: the version Trixie of Raspberry Pi OS;
- in the line `Mem:`, under `total`, a figure close to 8 GB. The exact figure on a Pi 5 with 8 GB:
  TO BE COMPLETED.

Raspberry Pi's AI software needs a Raspberry Pi 5 "with a 64-bit Raspberry Pi OS installation
(Trixie)" ([Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html)). If you see
something else, install this system first
([Raspberry Pi OS](https://www.raspberrypi.com/software/operating-systems/)). We wrote this page for
Trixie: we did not check the earlier version, Bookworm.

### Step 2 - Update the system and the firmware (not tested)

Raspberry Pi asks for the latest software and the latest firmware before its AI software
([Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html)):

```bash
sudo apt update
sudo apt full-upgrade -y
sudo rpi-eeprom-update -a
sudo reboot
```

The first two commands update the programs of the system. The third one updates the **firmware**,
the program kept in a memory chip of the board, which starts the Pi. The last one restarts the Pi.

**What you should see.** TO BE COMPLETED. After the restart, open a terminal again.

### Step 3 - Power, cooling and storage (not tested)

**Power.** For a Raspberry Pi 5, Raspberry Pi recommends its **27 W USB-C** power supply
([Raspberry Pi](https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/computers/raspberry-pi/power-supplies.adoc)).
With a supply that gives 5 A, like this one, the Pi gives more power to what you plug into its USB
ports: 1.6 A instead of 0.6 A (A, *amperes*, measure the current). With another supply, a USB disk
may get too little power. To check "the current status of power output to the USB ports", type:

```bash
vcgencmd get_config usb_max_current_enable
```

What it shows with the 27 W supply: TO BE COMPLETED.

**Cooling.** With the AI HAT+ 2, Raspberry Pi recommends both the **Active Cooler** (a heatsink with
a fan) on the Pi and the heatsink of the HAT
([Raspberry Pi](https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html)). Without
the HAT: we did not measure the temperature of a Pi during a session (TO BE COMPLETED).

**Storage.** Open WebUI takes about 2.0 GB once installed. We worked this figure out from its
packages for this processor; we did not measure it on a Pi. Add the model (part 2) and, with the AI
HAT+ 2, the model of the HAT (1.56 GB). A review found a 32 GB card tight: "a 64GB microSD card
would give more breathing room"
([CNX Software](https://www.cnx-software.com/2026/01/20/raspberry-pi-ai-hat-2-review-a-40-tops-ai-accelerator-tested-with-computer-vision-llm-and-vlm-workloads/),
blog). The memory used by Open WebUI and the model together, on a Pi with 8 GB: TO BE COMPLETED.

---

## Part 2 - Install Ollama and a model

*A technical part, after part 1.*

**On a Pi, the model is slow to start an answer.** A Raspberry Pi has no graphics card that Ollama
can use: for graphics cards, Ollama's download for Linux on this kind of processor has programs for
NVIDIA cards only, none for the graphics chip of the Pi (we read the list of its files, version
0.40.13).
So the model runs on the **processor**. Before it writes the first word of an answer, the model
reads the whole question, with the passages of your documents: about 2,000 tokens
([part 4 of the guide](README.md#part-4---build-the-chatbot)). The only figure we found for this
reading on a Pi 5 is in an article by Hailo: a question of 96 tokens took 2,039 milliseconds (about
2 seconds) before the first word, on the processor of a Pi 5, with the model Qwen2.5-1.5B in 4 bits
and llama.cpp, another program than Ollama
([Raspberry Pi](https://www.raspberrypi.com/news/when-and-why-you-might-need-the-raspberry-pi-ai-hat-plus-2/)).
The time of an answer with Ollama on a Pi: TO BE COMPLETED.

**Only the AI HAT+ 2?** If you have the AI HAT+ 2 and want to use only it, you may skip this part,
except the first command of step 1, which installs `curl`. Skip also step 7 of part 3:
[step 8 of the AI HAT+ 2](#step-8---connect-open-webui-to-hailo-ollama-not-tested) checks the
connection instead.

### Step 1 - Install Ollama

Raspberry Pi OS may not come with `curl`, the tool that the commands of this page use to download.
The installer of Ollama also needs `zstd`, a tool that unpacks its files: without it, it stops with
"This version requires zstd for extraction"
([Ollama](https://raw.githubusercontent.com/ollama/ollama/main/scripts/install.sh)). Whether
Raspberry Pi OS has them already: TO BE COMPLETED. This command installs them if they are missing:

<!-- ci raspberry-pi,raspberry-pi-hat stage=install check="curl --version" expect="libcurl/" check="zstd --version" expect="Zstandard" -->
```bash
sudo apt update && sudo apt install -y curl zstd
```

**What you should see.** `curl --version` answers with a version number, and `zstd --version` with
a line that contains `Zstandard`.

On Linux, the official installation of Ollama is one line ([Ollama](https://docs.ollama.com/linux)).
Its script recognises the processor of the Pi (`aarch64`, also called arm64); its documentation
never names the Raspberry Pi:

<!-- ci raspberry-pi stage=install check="ollama --version" expect="version" -->
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

It installs Ollama as a service that starts with the computer.

**What you should see.** `ollama --version` answers with a version number. On a machine of GitHub
(arm64, Ubuntu), this line installed TO BE COMPLETED. If `ollama --version` answers "command not
found", the download failed: check `curl --version` and `zstd --version`, then type the line again.

### Step 2 - Keep Ollama on this computer

Ollama also offers **cloud models**, which run on Ollama's servers, not on your computer. Turn this
off, so that no question can leave by mistake
([Ollama](https://docs.ollama.com/faq#how-do-i-disable-ollama-cloud-features)):

<!-- ci raspberry-pi stage=install -->
```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_NO_CLOUD=1"\n' | sudo tee /etc/systemd/system/ollama.service.d/no-cloud.conf
sudo systemctl daemon-reload && sudo systemctl restart ollama
```

The second command writes a small settings file for the Ollama service, and shows its two lines.
The third one starts Ollama again with this setting.

**What you should see.** Check the setting, then what Ollama says about it:

<!-- ci raspberry-pi stage=install expect="OLLAMA_NO_CLOUD=1" expect="Ollama cloud disabled: true" -->
```bash
systemctl show ollama -p Environment --no-pager | tr ' ' '\n' | grep -i ollama
sudo journalctl -u ollama --since today --no-pager | grep -i "cloud disabled"
```

The first command shows `OLLAMA_NO_CLOUD=1`. The second one shows a line with
`Ollama cloud disabled: true`. If not, type the three commands of the first box of this step again,
then these two.

Also keep Ollama **for this computer only**, as it is installed: Ollama has no accounts. If it were
opened to the network (for example with `OLLAMA_HOST=0.0.0.0`, an example of its documentation),
anyone on your Wi-Fi could use the model directly, without the rules of your chatbot. Only Open
WebUI is for the participants.

### Step 3 - Choose a model and read its licence

A model is a large file that you download once. Its **licence** says what you may do with it: read
it before you use a model with a group. Use only models without `cloud` in their name.

| Model | Download | Licence | What we know |
|---|---|---|---|
| `qwen2.5:1.5b` | 986 MB ([Ollama](https://ollama.com/library/qwen2.5:1.5b), read on 29 October 2026) | Apache 2.0 (all sizes of Qwen2.5 except 3B and 72B, [Ollama](https://ollama.com/library/qwen2.5)) | 9.97 tokens per second on the processor of a Pi 5, with Ollama and "a simple prompt" (a short question), on an undated page that does not say how much memory the Pi had ([Stratosphere](https://stratospherelinuxips.readthedocs.io/en/develop/_sources/immune/research_rpi_llm_performance.md.txt)); its answers to our 11 questions: TO BE COMPLETED |
| `qwen2.5:7b` | 4.7 GB | Apache 2.0 (as above) | the model of the [Linux page](linux.md#step-3---choose-a-model-and-read-its-licence); on a Pi 5 with 8 GB, memory and speed: TO BE COMPLETED |

We suggest `qwen2.5:1.5b` on a Pi: it is about five times smaller than `qwen2.5:7b`, and its licence
is Apache 2.0. But we did not measure its answers: check them on your topic first
([part 5](README.md#part-5---test-it)). `qwen2.5:3b` is not in this table: its licence is not Apache
2.0.

The Apache 2.0 and MIT licences allow the use by an association, and they have no rule on minors.
Other families of models have their own licences and use policies: read them first. For example,
the [Llama 3.1 policy](https://www.llama.com/llama3_1/use-policy/) has rules about minors, and the
[Gemma terms](https://ai.google.dev/gemma/terms) let Google restrict, even remotely, any use it
reasonably believes breaks those terms. We did not measure these models.

### Step 4 - Download the model

<!-- ci raspberry-pi stage=install -->
```bash
ollama pull qwen2.5:1.5b
```

Then check that it runs, and where:

<!-- ci raspberry-pi stage=install expect="PROCESSOR" expect="100% CPU" -->
```bash
ollama run qwen2.5:1.5b "Hello" && ollama ps
```

**What you should see.** An answer, then a line for the model with `100% CPU` in the column
**PROCESSOR**: the model is on the processor. On a Pi, this is expected: it has no graphics card for
Ollama. The first answer takes longer, while the model loads: TO BE COMPLETED on a Pi.

---

## Part 3 - Start Open WebUI

*A technical part.* Open WebUI is a Python program. You install it in a folder of its own,
`~/owui-local`, and the computer runs it as a service, on the same computer as Ollama. In this
part, only this computer can open it. You open it to your local network in
[part 6](README.md#part-6---open-it-to-your-group), when your administrator account exists.

### Step 1 - Install uv

**uv** is a free tool that installs Python programs, and the version of Python they need. Open
WebUI 0.12.4 needs Python 3.11 or 3.12 ([PyPI](https://pypi.org/pypi/open-webui/0.12.4/json)).
Raspberry Pi OS Trixie comes with Python 3.13, which is too new
([Debian](https://packages.debian.org/trixie/python3)). This is why Raspberry Pi's own documentation
runs Open WebUI in Docker: "Open WebUI is incompatible with Python 3.13 (as used on Raspberry Pi OS
Trixie)" ([Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html)). uv
downloads Python 3.12 for Open WebUI instead, without changing the Python of the Pi. uv supports
this kind of processor (Linux on aarch64) at its "Tier 2": uv is built for it, but its own tests
are not run on it
([uv](https://github.com/astral-sh/uv/blob/0.13.6/docs/reference/policies/platforms.md)).

Do this whole part in a normal account of the computer, the one you will use for Open WebUI, not
as `root`: `whoami` must not answer `root`. Open WebUI will run with the rights of this account.

<!-- ci raspberry-pi,raspberry-pi-hat stage=install check="uv --version" expect="uv 0.13.6" -->
```bash
curl -LsSf https://astral.sh/uv/0.13.6/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

The first command installs uv for your user, in `~/.local/bin`. The second one lets this terminal
find it; the next terminals find it by themselves.

**What you should see.** Type `uv --version`: it answers a line that starts with `uv 0.13.6`. If uv
was already installed in `~/.local/bin`, the installer has replaced it with this version.

> [!IMPORTANT]
> **You followed an earlier version of this guide, with uv 0.13.1?** Update uv: type
> `uv self update`. uv 0.13.1 has a security problem
> ([GHSA-hq85-5cpj-mr62](https://github.com/astral-sh/uv/security/advisories/GHSA-hq85-5cpj-mr62)),
> fixed in uv 0.13.4. This command works for uv installed with the command above
> ([uv](https://docs.astral.sh/uv/getting-started/installation/#upgrading-uv)).

### Step 2 - Create a virtual environment

A **virtual environment** (often called a *venv*) is a folder that holds the programs installed for
one project, apart from the rest of the computer. It uses the Python that uv downloaded. Deleting
the folder deletes these programs. Create the folder of Open WebUI, and its virtual environment
inside, named `venv`:

<!-- ci raspberry-pi,raspberry-pi-hat stage=install check="python --version" expect="Python 3.12" -->
```bash
mkdir -p ~/owui-local && chmod 700 ~/owui-local && cd ~/owui-local
uv venv --managed-python --python 3.12 venv
source venv/bin/activate
```

`chmod 700` lets only your account open this folder: it will hold the conversations of your group.
The second command downloads Python 3.12 (about 30 MB for this processor,
[python-build-standalone](https://github.com/astral-sh/python-build-standalone/releases/tag/20261026))
the first time; `--managed-python` makes uv use its own copy, the one we tested, even if the
computer already has a Python 3.12. The third one **activates** the virtual environment: in this
terminal, `python` and the programs you install now are those of `venv`.

**What you should see.** `(venv)` at the start of the line where you type. If you close the
terminal before the end of this part, open a new one and type
`cd ~/owui-local && source venv/bin/activate` before you go on.

### Step 3 - Install Open WebUI

<!-- ci raspberry-pi,raspberry-pi-hat stage=install check="uv pip show open-webui" expect="Version: 0.12.4" -->
```bash
uv pip install --torch-backend cpu "torch<=2.9.1" open-webui==0.12.4
```

This installs Open WebUI 0.12.4 in `venv`, with the programs it needs. Worked out from its packages
for this processor, without a Pi: about 620 MB to download for Open WebUI and its programs, and
2.0 GB once on the disk. Time on a Pi: TO BE COMPLETED. We measured the answers with an earlier
version, 0.11.4 ([About](README.md#about)). Open WebUI uses **torch** to search in your documents.
`--torch-backend cpu` installs the version of torch for the processor. `torch<=2.9.1` is the
version in Open WebUI's own installation, the one we measured.

Then download the small model that Open WebUI uses to search in your documents (about 90 MB; time
on a Pi: TO BE COMPLETED). With the settings of this guide, Open WebUI never downloads anything by
itself, so it needs it now:

<!-- ci raspberry-pi,raspberry-pi-hat stage=install -->
```bash
SENTENCE_TRANSFORMERS_HOME=$HOME/owui-local/data/cache/embedding/models python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

**What you should see.** `uv pip show open-webui` shows `Version: 0.12.4`. The second command may
show a warning about "unauthenticated requests" and a "LOAD REPORT" with the word `UNEXPECTED`:
they are normal. It must not end with `Error`.

### Step 4 - Get the settings for a group

The file [`openwebui.env`](openwebui.env) of this guide holds the settings we use with young
people:

- Open WebUI is set not to send anything out by itself (no statistics, no update checks, no web
  search);
- the participants do not see the buttons to change a chatbot, or to upload files or photos. This
  hides the buttons; it is not a lock: a participant with technical skills could still send a file;
- a banner asks them not to write personal information;
- a sign-in lasts 12 hours, and the participants do not see your name and e-mail;
- Open WebUI writes only warnings and errors in the computer's log (the *journal*), not the e-mail
  used at each sign-in or the address of each phone.

Each line of the file is explained. Download it into the folder of Open WebUI:

<!-- ci raspberry-pi,raspberry-pi-hat stage=install -->
```bash
cd ~/owui-local
curl -fsSLO https://raw.githubusercontent.com/Youth-AI-Lab/yal-local-ai-guide/main/openwebui.env
```

Open WebUI saves most of these settings in its own data at its very first start. After that,
changing the file has no effect on them: you change them in the **Admin Panel**. For example, to
show the banner in the language of your group, change its text after
[step 6](#step-6---create-your-administrator-account), in **Admin Panel** → **Settings** →
**General**, in the part about banners ("Create announcements shown to users in the app."), then
click **Save**.

### Step 5 - Start Open WebUI as a service

Copy this whole block into the terminal, from `sudo tee` to the second `EOF`, and press `Enter`.
It writes the file of the service, with the name of your user and the paths of your folder:

<!-- ci raspberry-pi,raspberry-pi-hat stage=install -->
```bash
sudo tee /etc/systemd/system/owui-local.service >/dev/null <<EOF
[Unit]
Description=Open WebUI for the group
After=network-online.target ollama.service hailo-ollama.service
Wants=network-online.target

[Service]
User=$USER
WorkingDirectory=$HOME/owui-local
EnvironmentFile=$HOME/owui-local/openwebui.env
Environment=DATA_DIR=$HOME/owui-local/data
Environment=SENTENCE_TRANSFORMERS_HOME=$HOME/owui-local/data/cache/embedding/models
ExecStart=$HOME/owui-local/venv/bin/open-webui serve --host 127.0.0.1 --port 3000
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

This service:

- starts Open WebUI on **port 3000** of this computer, for this computer only (`--host 127.0.0.1`),
  with the settings of `openwebui.env`;
- keeps its data (accounts, chatbots, conversations, documents) in the folder
  `~/owui-local/data`;
- starts it again after a restart of the computer, and if it stops by accident.

The line `After=` names both servers of models, Ollama and hailo-ollama (the program of the
[AI HAT+ 2](#with-the-ai-hat-2)), so that Open WebUI starts after the one you installed. The
computer skips a name that is not installed.

First check that no other program uses port 3000: type `ss -ltn 'sport = :3000'`. It must show only
one line, the titles. If a second line shows `:3000`, another program uses this port, maybe another
Open WebUI: stop it first. Otherwise the next block could say "Open WebUI is ready" for this other
program.

Then start Open WebUI, and wait until it is ready:

<!-- ci raspberry-pi,raspberry-pi-hat stage=install expect="Open WebUI is ready" check="ss -ltn" expect="127.0.0.1:3000" -->
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now owui-local
until curl -sf http://localhost:3000/health >/dev/null; do sleep 5; done; echo "Open WebUI is ready"
```

**What you should see.** `Open WebUI is ready`. The first start prepares its database: on a Pi, it
takes TO BE COMPLETED.
If nothing appears after 5 minutes, press `Ctrl+C` and type
`sudo journalctl -u owui-local -n 20 --no-pager`. A line with "address already in use" means that
another program of the computer uses port 3000: stop this program first.

> [!TIP]
> The file `.webui_secret_key` in `~/owui-local` keeps the sign-ins valid when Open WebUI starts
> again. Keep it with the folder.

### Step 6 - Create your administrator account

> [!NOTE]
> Open WebUI speaks the language of your browser: in a French browser, **Get started** reads
> **Démarrer**. This guide gives the English names. To see them, once your account exists: your
> name at the bottom left → **Settings** → **General** → **Language** → **English (US)**. This
> changes the language in this browser only: each participant sees the language of their own
> browser.

Open <http://localhost:3000> on this computer. On the welcome page, click **Get started**. In the
form **Get started with Group chatbots (Open WebUI)**, type:

- as name, a role rather than your own name, for example `Facilitator`;
- as e-mail, an address that is only your login, for example `facilitator@group.local` (Open WebUI
  sends no mail to it);
- a strong password. Keep it in your organisation's password manager: you are the only
  administrator, and this guide has no command to show it again.

Click **Create Admin Account**.

**What you should see.** First a window **What's New in Group chatbots (Open WebUI)**: click
**Okay, Let's Go!** at the bottom (the participants never see it). Then the chat page of Open WebUI. Your name at the bottom left opens a menu with **Admin Panel**: you are the
administrator. **The first account becomes the administrator**, and
Open WebUI then **closes the sign-ups** by itself. Nobody else can create an account until you open
them in [part 6](README.md#part-6---open-it-to-your-group).

### Step 7 - Check the connection to Ollama

Click **New Chat**. In the list of models, at the bottom right of the message box, choose
`qwen2.5:1.5b` (Open WebUI may have chosen another model of Ollama for you). Ask "Hello, who are
you?": the first answer is slower, while the model loads. Time on a Pi: TO BE COMPLETED. If the list
is empty, see [Troubleshooting](README.md#the-model-list-is-empty). If the answer is "does not
support tools", see [this entry](README.md#the-answer-is-does-not-support-tools).

Only the AI HAT+ 2, no part 2? Skip this step:
[step 8 of the AI HAT+ 2](#step-8---connect-open-webui-to-hailo-ollama-not-tested) checks the
connection.

---

## With the AI HAT+ 2

**The AI HAT+ 2 is an extra board for the Raspberry Pi 5 only.** It has a Hailo-10H chip, made for
AI, and its "own 8 GB onboard memory"
([Raspberry Pi](https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html)). Its price
is "$200" on its product page, checked on 29 October 2026
([Raspberry Pi](https://www.raspberrypi.com/products/ai-hat-plus-2/)). Do this section after part 3,
and before part 4 of the guide.

**A different server of models.** On the HAT, the model does not run with Ollama but with Hailo's
**hailo-ollama**, version 5.1.1, the version that Raspberry Pi documents
([Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html)). It speaks to Open
WebUI like Ollama, but on port **8000**, and it has no `ollama` command
([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/main/docs/USAGE.rst)). Its models
are fixed: each has a context window of **2,048 tokens**, set when the model was built, and no
setting changes it
([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/docs/MODELS.rst),
[HailoRT](https://github.com/hailo-ai/hailort/blob/v5.1.1/hailort/libhailort/include/hailo/genai/llm/llm.hpp)).
A question to the chatbot of part 4, with the passages of its
documents, was about 2,030 tokens on our laptop, with another model
([part 4 of the guide](README.md#part-4---build-the-chatbot)). So on the HAT, build a chatbot
**without documents**, for short conversations
([step 10](#step-10---build-chatbots-for-the-ai-hat-2-not-tested)).

**One question at a time.** hailo-ollama answers one request at a time
([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/docs/USAGE.rst)): the others
wait their turn (read in
[its code](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/src/library/generation_context/generation_context.cpp)).
Hailo's own figures for `qwen2:1.5b` are 7.37 seconds to load, 0.32 seconds to the first word, and
8.18 tokens per second, without saying on which computer, or with which length of question
([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/docs/MODELS.rst)). Two
reviews found the processor of the Pi faster at writing answers: "The Pi's built-in CPU trounces
the Hailo 10H." ([Jeff Geerling](https://www.jeffgeerling.com/blog/2026/raspberry-pi-ai-hat-2/),
blog), and the same result in
[CNX Software](https://www.cnx-software.com/2026/01/20/raspberry-pi-ai-hat-2-review-a-40-tops-ai-accelerator-tested-with-computer-vision-llm-and-vlm-workloads/)
(blog), with another board for the processor. Hailo writes that the HAT is strongest when it reads
long questions, not when it writes long answers
([Raspberry Pi](https://www.raspberrypi.com/news/when-and-why-you-might-need-the-raspberry-pi-ai-hat-plus-2/)).
What it brings to a group: TO BE COMPLETED.

**Small models.** Raspberry Pi warns: "Smaller LLMs like these are not designed to match the
knowledge set available to the larger models"
([Raspberry Pi](https://www.raspberrypi.com/news/introducing-the-raspberry-pi-ai-hat-plus-2-generative-ai-on-raspberry-pi-5/)).

> [!IMPORTANT]
> **Adult supervision.** The product brief of the AI HAT+ 2 says: "Operation of this device requires
> adult supervision."
> ([Raspberry Pi](https://pip-assets.raspberrypi.com/categories/1319-raspberry-pi-ai-hat-2/documents/RP-009655-MM-6-raspberry-pi-ai-hat-plus-2-product-brief.pdf)).
> Keep the Pi and its HAT with the facilitator, not in the participants' hands.

> [!NOTE]
> **Not tested with a real AI HAT+ 2.** Steps 1, 2, 5 and 7 to 10 need the board (and steps 8 to
> 10 a browser). On a machine of GitHub, the test of this guide installs the real package of
> hailo-ollama 5.1.1 (steps 3 and 4), but a small program runs in place of hailo-ollama and the HAT
> (steps 5 to 7): the real `/usr/bin/hailo-ollama` needs HailoRT, the Hailo software that talks to
> the chip (installed at step 2), and the chip itself. The test does steps 8
> to 10 through Open WebUI's programming interface ([`ci/README.md`](ci/README.md)).

### Step 1 - Fit the AI HAT+ 2 (not tested)

Raspberry Pi's documentation shows each step with pictures
([Raspberry Pi](https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html)). Follow
it. In short:

1. Unplug the Pi from its power supply.
2. Fit the **Active Cooler** on the Pi.
3. Fit the heatsink of the HAT on the HAT, before you mount the HAT on the Pi. Do not remove the
   Active Cooler or the heatsink once fitted: Raspberry Pi writes that it can damage them.
4. Fit the four spacers on the Pi (small posts that hold the HAT above the Pi). Then fit the GPIO
   stacking header (a connector with long pins) on the GPIO pins of the Pi, the pins along one of
   its edges.
5. Connect the ribbon cable (the flat PCIe cable, which carries the data between the Pi and the
   HAT) to the Pi, with "the metallic contact points … facing inwards
   (towards the USB ports)", then mount the HAT on the spacers and connect the cable to the HAT.

There is no command in this step.

### Step 2 - Install the driver of the AI HAT+ 2 (not tested)

The **driver** of the HAT is the program that lets the system use it. Raspberry Pi installs it with
these commands ([Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html)):

```bash
sudo apt install dkms
sudo apt install hailo-h10-all
sudo reboot
```

`dkms` is a tool that builds the driver again each time the core of the system (the *kernel*) is
updated. `hailo-h10-all` installs the driver and the firmware of the chip, and Hailo's libraries.
The last command restarts the Pi. After the restart, open a terminal and check the HAT
([Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html)):

```bash
hailortcli fw-control identify
dmesg | grep -i hailo
```

**What you should see.** The first command describes the chip and its firmware. "AI HAT+ and AI
HAT+ 2 might show `<N/A>` for `Serial Number`, `Part Number` and `Product Name`. This is expected"
([Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html)). The exact text for
the Hailo-10H of the AI HAT+ 2: TO BE COMPLETED (the example of the documentation is another chip).
The second command shows the messages of the system about Hailo. If it answers that the operation
is not permitted, type `sudo dmesg | grep -i hailo` (not tested).

> [!WARNING]
> Never install `hailo-all`: it is the package of the other AI boards of Raspberry Pi, and "These
> packages can't co-exist"
> ([Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html)). The same
> documentation also shows how to make the connector of an AI board faster ("Enable PCIe Gen 3.0"),
> for its older AI Kit only. Skip it: for the AI HAT+ 2, "the setting is automatically applied".

### Step 3 - Install hailo-ollama

Raspberry Pi links the package of hailo-ollama 5.1.1 on Hailo's server
([Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html)). Download it into
your home folder, check it, and install it:

<!-- ci raspberry-pi-hat stage=install expect="arm64.deb: OK" check="dpkg -s hailo-gen-ai-model-zoo" expect="Version: 5.1.1" -->
```bash
cd ~
curl -fsSLO https://dev-public.hailo.ai/2025_12/Hailo10/hailo_gen_ai_model_zoo_5.1.1_arm64.deb
echo "17d5b476320b72ec199032e7a7b87ba72cb51311d56a9f0604213b7a9056deb9  hailo_gen_ai_model_zoo_5.1.1_arm64.deb" | sha256sum -c && sudo dpkg -i hailo_gen_ai_model_zoo_5.1.1_arm64.deb
```

The second command downloads the package (about 8 MB). The third line computes its fingerprint, and
compares it with the one we measured on 29 October 2026. Only if they match (`&&`), it installs the
package, as in Raspberry Pi's documentation.

**What you should see.** `hailo_gen_ai_model_zoo_5.1.1_arm64.deb: OK`: the file is exactly the one
we checked. Then the messages of the installation. Type `dpkg -s hailo-gen-ai-model-zoo`: it shows
`Version: 5.1.1`. If it says `FAILED`, nothing was installed: stop, Hailo changed the file.

The package is named `hailo-gen-ai-model-zoo`, not hailo-ollama. It installs the program
`/usr/bin/hailo-ollama`, its settings file `/etc/xdg/hailo-ollama/hailo-ollama.json`, and the list
of its models. It does not come from the system's list of programs: the updates of step 2 of part 1
never update it. hailo-ollama is under the MIT licence
([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/README.rst)).

**Only your account may change the models.** The package makes the folder
`/usr/share/hailo-ollama/models` writable by every account of the Pi (we read this in the package).
This folder holds, for each model, the text that hailo-ollama adds around every question. Any
program of the Pi could change it, or replace a model. Take this right back:

<!-- ci raspberry-pi-hat stage=install check="stat -c '%A %U %n' /usr/share/hailo-ollama/models /usr/share/hailo-ollama/models/blob" expect="drwxr-xr-x root /usr/share/hailo-ollama/models" -->
```bash
sudo chmod -R go-w /usr/share/hailo-ollama/models
sudo install -d -o "$USER" -g "$USER" -m 755 /usr/share/hailo-ollama/models/blob
```

The first command takes the right to write from every account except the owner of the folder,
`root`, the administrator of the system. The second one makes the folder `blob`, where hailo-ollama
puts the models it downloads ([step 7](#step-7---download-a-model-for-the-ai-hat-2-not-tested)), and
gives it to your account, the one that runs hailo-ollama
([step 5](#step-5---start-hailo-ollama-as-a-service-not-tested)): hailo-ollama writes nowhere else
(read in its code). We tried these two commands on the package in a container of a Linux PC, not on
a Pi.

**What you should see.** No message. Type
`stat -c '%A %U %n' /usr/share/hailo-ollama/models /usr/share/hailo-ollama/models/blob`: it shows
`drwxr-xr-x root` for the first folder, and `drwxr-xr-x` with the name of your account for `blob`.

> [!IMPORTANT]
> **Stay on version 5.1.1.** It is the version that Raspberry Pi documents, and the version of the
> driver of step 2 (5.1.1). Hailo has published newer versions. In version 5.3.0, a bug broke the
> questions of Open WebUI with documents, and conversations with messages of several lines; Hailo's
> staff confirmed it
> ([Hailo forum](https://community.hailo.ai/t/json-config-hailo-internal-failure-8/19159)). The
> names of the models also change between versions
> ([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/main/docs/CHANGELOG.rst)).

### Step 4 - Keep hailo-ollama on this computer

hailo-ollama has no accounts. As installed, it listens on every network of the Pi:
`"host": "0.0.0.0"` in its settings file
([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/config/hailo-ollama.json)).
Anyone on your Wi-Fi could then use the model directly, without the rules of your chatbot. Keep it
for this computer only:

<!-- ci raspberry-pi-hat stage=install expect="127.0.0.1" -->
```bash
sudo sed -i 's/"host": "0.0.0.0"/"host": "127.0.0.1"/' /etc/xdg/hailo-ollama/hailo-ollama.json
grep '"host"' /etc/xdg/hailo-ollama/hailo-ollama.json
```

The first command replaces `0.0.0.0` (every network) with `127.0.0.1` (this computer only) in the
settings file. The second one shows the lines of the file that set an address.

**What you should see.** Two lines:

```
        "host": "127.0.0.1",
        "host": "dev-public.hailo.ai",
```

The first one is the address of hailo-ollama, now for this computer only. The second one is Hailo's
server, where hailo-ollama downloads the models: leave it. Only Open WebUI is for the participants.

The setting `OLLAMA_HOST` of Ollama does not work with hailo-ollama 5.1.1: it came with version
5.3.0 ([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/main/docs/CHANGELOG.rst)).

> [!WARNING]
> **Never install the package again over itself.** Its removal script deletes the folder
> `/usr/share/hailo-ollama`, with the list of the models and the models you downloaded, even when
> the same package is being installed again. The installation then stops with an error, and
> hailo-ollama no longer starts. We saw this with the package in a container of a Linux PC, not on
> a Pi. To install it again, first remove it with `sudo dpkg -r hailo-gen-ai-model-zoo`, then do
> steps 3, 4 and 7 again: a new installation also puts back `0.0.0.0`, and the rights that step 3
> took back.

### Step 5 - Start hailo-ollama as a service (not tested)

Raspberry Pi's documentation starts `hailo-ollama` by hand, in a terminal that must stay open, and
the package has no service of its own. This step makes it a service, like Open WebUI. Copy this
whole block into the terminal, from `sudo tee` to the second `EOF`, and press `Enter`:

<!-- ci raspberry-pi-hat stage=install -->
```bash
sudo tee /etc/systemd/system/hailo-ollama.service >/dev/null <<EOF
[Unit]
Description=hailo-ollama, the model server of the AI HAT+ 2
After=network-online.target
Wants=network-online.target

[Service]
User=$USER
Environment=XDG_CONFIG_HOME=/etc/xdg
Environment=XDG_DATA_HOME=/usr/share
Environment=HAILORT_LOGGER_PATH=NONE
ExecStart=/usr/bin/hailo-ollama
StandardOutput=null
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

This service:

- runs hailo-ollama with your account (`User=`), as when you type `hailo-ollama` in a terminal;
- reads only the settings file of step 4 and the folder of models of step 3 (the two lines
  `XDG_...`), never a copy in your home folder;
- keeps no log file (`HAILORT_LOGGER_PATH=NONE`) and sends its messages nowhere
  (`StandardOutput=null`), for the reasons below;
- starts it with the Pi, and again if it stops by accident (`Restart=on-failure`), as for Open
  WebUI.

**Why the two lines `XDG_...`.** hailo-ollama 5.1.1 looks for its settings first in your home
folder, in `~/.config/hailo-ollama`, and for its models in `~/.local/share/hailo-ollama`. Only if
these folders do not exist does it use those of the package (read in
[its code](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/src/apps/server/main.cpp)).
Hailo's own instructions for another way to install it create these folders, with `"host":
"0.0.0.0"`
([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/docs/USAGE.rst)). With
these two lines, the service uses `/etc/xdg/hailo-ollama` and `/usr/share/hailo-ollama` whatever
your home folder holds, so the setting of step 4 is always the one used.

**Why `StandardOutput=null`.** hailo-ollama 5.1.1 writes each question it receives, with the whole
conversation, to its *standard output*, the text that a program shows in its terminal ("got prompt"
in [its code](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/src/library/generation_context/generation_context.cpp)).
Its other messages go there too (we read this in its code), and the warnings of HailoRT, the Hailo
software that hailo-ollama uses to talk to the chip, go to its *standard error*, which systemd sends
to the same place. As a service, this output would go to the journal of the computer, with the
questions of your group. With this line, it goes nowhere. The journal still says when the service
starts, stops or fails, but the messages of hailo-ollama are not there: to see them, see
[Troubleshooting](#hailo-ollama-does-not-start-ai-hat-2).

**Why `HAILORT_LOGGER_PATH=NONE`.** HailoRT 5.1.1 also writes its messages to a file,
`~/.hailo/hailort/hailort.log`, and to a file `hailort.log` in the folder where it starts. This
line turns both off (read in
[its code](https://github.com/hailo-ai/hailort/blob/v5.1.1/hailort/libhailort/src/utils/hailort_logger.cpp)).
In the code we read, these messages hold no question; what they hold on a Pi: TO BE COMPLETED.

First check that no other program uses port 8000: type `ss -ltn 'sport = :8000'`. It must show only
one line, the titles. If a second line shows `:8000`, another program uses this port: stop it
first. Otherwise the next block could say "hailo-ollama is ready" for this other program, and Open
WebUI would later send the questions of your group to it.

Then start hailo-ollama, and wait until it is ready:

<!-- ci raspberry-pi-hat stage=install expect="hailo-ollama is ready" check="ss -ltn 'sport = :8000'" expect="127.0.0.1:8000" -->
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now hailo-ollama
until curl -sf http://127.0.0.1:8000/ >/dev/null; do sleep 2; done; echo "hailo-ollama is ready"
```

**What you should see.** `hailo-ollama is ready`. Time on a Pi: TO BE COMPLETED. Then type
`ss -ltn 'sport = :8000'`: it shows `127.0.0.1:8000`, not `0.0.0.0:8000`. If nothing appears after a
minute, press `Ctrl+C` and type `sudo journalctl -u hailo-ollama -n 20 --no-pager` (see
[Troubleshooting](#hailo-ollama-does-not-start-ai-hat-2)).

### Step 6 - Choose a model for the AI HAT+ 2 and read its licence

hailo-ollama 5.1.1 offers five models. They are made for the HAT, and you cannot add others
([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/docs/USAGE.rst)). As in
[part 2](#step-3---choose-a-model-and-read-its-licence), read the licence of a model before you use
it with a group. Three of them are for conversations:

| Model | Download | Licence | Hailo's figures (load / first word / tokens per second) |
|---|---|---|---|
| `qwen2:1.5b` | 1.56 GB | Apache 2.0 | 7.37 s / 0.32 s / 8.18 |
| `qwen2.5-instruct:1.5b` | 1.64 GB | the licence file of Qwen2.5, linked by Hailo: read it | 8.45 s / 0.37 s / 6.95 |
| `llama3.2:3b` | 3.13 GB | the Llama 3.2 Community License: read it, and its use policy | 12.61 s / 1.47 s / 2.67 |

The names come from the package of version 5.1.1; the sizes, figures and licence links from Hailo
([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/docs/MODELS.rst)). All have
a context of 2,048 tokens. Hailo does not say on which computer, or with which length of question,
it measured.

We suggest `qwen2:1.5b`: its licence is Apache 2.0, it is the example of Raspberry Pi's
documentation, and every version of hailo-ollama so far, from 5.1.1 to 5.4.0, keeps its name (read
in the [lists of models](https://github.com/hailo-ai/hailo_model_zoo_genai/tree/v5.4.0/models/manifests)
of each version; `qwen2.5-coder:1.5b` too, but it is made for code). The two
other models of the list are left out: `qwen2.5-coder:1.5b` is made for computer code, and Hailo's
table repeats the load and first-word figures of `llama3.2:3b` on the line of
`deepseek_r1_distill_qwen:1.5b`, which looks like a mistake.

### Step 7 - Download a model for the AI HAT+ 2 (not tested)

hailo-ollama has no `ollama` command: `curl` sends it requests, as in Raspberry Pi's documentation
([Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html),
[Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/docs/USAGE.rst)). First list
the models it can download:

<!-- ci raspberry-pi-hat stage=install expect="qwen2:1.5b" -->
```bash
curl --silent http://localhost:8000/hailo/v1/list
```

**What you should see.** The five names of step 6, in one line (read in the code of hailo-ollama):

```
{"models":["deepseek_r1_distill_qwen:1.5b","llama3.2:3b","qwen2.5-coder:1.5b","qwen2.5-instruct:1.5b","qwen2:1.5b"]}
```

Then download `qwen2:1.5b`, 1.56 GB from Hailo's server (`dev-public.hailo.ai`). Time on a Pi: TO BE
COMPLETED.

<!-- ci raspberry-pi-hat stage=install expect="success" -->
```bash
curl --silent http://localhost:8000/api/pull -H 'Content-Type: application/json' -d '{ "model": "qwen2:1.5b", "stream" : true }'
```

**What you should see.** Lines with `"status":"pulling"` and growing numbers, then
`{"status":"verifying sha256 digest"}` and `{"status":"success"}`. The model goes to the folder
`/usr/share/hailo-ollama/models/blob` (read in the code of hailo-ollama, and seen by
[CNX Software](https://www.cnx-software.com/2026/01/20/raspberry-pi-ai-hat-2-review-a-40-tops-ai-accelerator-tested-with-computer-vision-llm-and-vlm-workloads/)
on a Pi 5).

Then ask it a question, the one of Raspberry Pi's documentation:

<!-- ci raspberry-pi-hat stage=install expect="done_reason" check="curl --silent http://localhost:8000/api/ps" expect="qwen2:1.5b" -->
```bash
curl --silent http://localhost:8000/api/chat -H 'Content-Type: application/json' -d '{"model": "qwen2:1.5b", "messages": [{"role": "user", "content": "Translate to French: The cat is on the table."}]}'
```

**What you should see.** Many lines in braces `{…}`. Each holds a small piece of the answer, one
token (a word or a part of a word), after `"content":`. The last line has `"done":true`. Then type `curl --silent http://localhost:8000/api/ps`: it shows the model loaded on
the HAT, `qwen2:1.5b`
([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/main/docs/USAGE.rst)). It stays
loaded 5 minutes after the last question (read in the code of hailo-ollama).

Then check that this question did not reach the journal of the computer:

<!-- ci raspberry-pi-hat stage=install expect="No question in the journal" -->
```bash
sudo journalctl -u hailo-ollama --since today --no-pager | grep "got prompt" || echo "No question in the journal"
```

**What you should see.** `No question in the journal`. If lines with `got prompt` appear, the file
of the service lacks `StandardOutput=null`: write it again ([step 5](#step-5---start-hailo-ollama-as-a-service-not-tested)),
then type `sudo systemctl daemon-reload && sudo systemctl restart hailo-ollama`.

### Step 8 - Connect Open WebUI to hailo-ollama (not tested)

Open WebUI talks to hailo-ollama as it talks to Ollama, with a connection of the kind **Ollama
API**, as in the documentation of Raspberry Pi and Hailo
([Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html),
[Hailo](https://github.com/hailo-ai/hailo-apps/blob/main/hailo_apps/python/gen_ai_apps/hailo_ollama/README.md)).
Not the kind OpenAI: hailo-ollama has no list of models in that form.

> [!IMPORTANT]
> **This step replaces the connection to Ollama.** If you did part 2, its models leave the list of
> Open WebUI, and the chatbots built on them stop answering. Using both in one Open WebUI: not
> tested (TO BE COMPLETED).

In Open WebUI, open **Admin Panel** → **Settings** → **Connections**. Check that **Ollama API** is
on. Under **Manage Ollama API Connections**, click the gear icon (**Configure**) at the end of the
address line, not the arrow (**Manage**). In **URL**, delete the address that is there
(`http://127.0.0.1:11434`, the address of Ollama), and type `http://127.0.0.1:8000`. Click the two
circling arrows (**Verify Connection**) to the right of it, then click **Save**.

**What you should see.** **Verify Connection** shows a message of success (its exact text: TO BE
COMPLETED). On a machine of GitHub, the test of this guide checks, with the small program that
stands in for hailo-ollama, that Open WebUI receives the version written in the code of
hailo-ollama 5.1.1, `0.5.1`.

### Step 9 - Set the model of the AI HAT+ 2 (not tested)

By default, Open WebUI 0.12.4 sends a list of its own tools with each question (the mode
**Native**, the default since Open WebUI 0.10.0,
[Open WebUI](https://github.com/open-webui/open-webui/blob/main/CHANGELOG.md)). hailo-ollama 5.1.1
expects text in that place
([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/src/library/dto/DTOs.hpp)),
and refuses the question with an error 500, "Node is NOT a STRING". Users on Hailo's forum fixed it
with the two settings below, with hailo-ollama 5.1.1 and Open WebUI 0.11.0
([Hailo forum](https://community.hailo.ai/t/hailo-ollama-return-type-unsuitable-for-open-webui/19327)).
We did not test them with 0.12.4 on a Pi. On a machine of GitHub, the test of this guide checks
them with the small program that stands in for hailo-ollama and the HAT.

Your name at the bottom left → **Admin Panel** → **Settings** → **Models**. Click the pencil
(**Edit**) on the line of `qwen2:1.5b`, and change two things:

1. click the row **Advanced Params** to open it, find **Function Calling**, and click its button
   until it reads **Legacy**. The row **Advanced Params** then reads **1 modified**;
2. click the row **Capabilities** to open it, and switch off **Builtin Tools**.

These settings protect the model when someone uses it directly: your test below, and the safety net
of part 6. Each chatbot built on it needs them too ([step 10](#step-10---build-chatbots-for-the-ai-hat-2-not-tested)).

Click **Save & Update**. Then click **New Chat**, choose `qwen2:1.5b` in the list of models, and ask
"Hello, who are you?". Time on a Pi: TO BE COMPLETED.

In part 6 of the guide ([before the first session, step 3](README.md#before-the-first-session)),
the safety net of this model has three settings: **Function Calling: Legacy**, **Builtin Tools**
off, and a **System Prompt**. You did the first two here. In part 6, add the System Prompt, and
check that the first two are still set.

### Step 10 - Build chatbots for the AI HAT+ 2 (not tested)

Follow [part 4 of the guide](README.md#part-4---build-the-chatbot), with these differences for
**every** chatbot on the HAT:

1. **Base model.** In **Base Model (From)**, choose `qwen2:1.5b`.
2. **Function Calling: Legacy**, as in part 4.
3. **Builtin Tools off.** Click the row **Capabilities**, and switch off **Builtin Tools**, as in
   step 9. With the settings by default (**Native**, **Builtin Tools** on), Open WebUI sends its
   tools, and hailo-ollama refuses the question (error 500). The settings of the model of step 9
   do not pass to a chatbot built on it (our test on 29 October 2026: Open WebUI 0.12.4 on a Linux
   PC, with the small program that stands in for hailo-ollama, not the HAT).
4. **No knowledge.** Do not add documents: they would not fit in 2,048 tokens.
5. **num_ctx.** Leave it on **Default**. hailo-ollama ignores it: its context is fixed
   ([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/src/library/dto/DTOs.hpp),
   [HailoRT](https://github.com/hailo-ai/hailort/blob/v5.1.1/hailort/libhailort/include/hailo/genai/llm/llm.hpp)).

**The instructions must fit, with the conversation, in 2,048 tokens.** We counted the filled
examples of the Open WebUI guide with the tokenizer of Qwen2, the tool that cuts text into tokens
for this model: 621 tokens for `topic-assistant`, 951 for `activity-guide` and 990 for
`project-coach` (the text below their line `---`). You cannot count tokens yourself: keep your
instructions shorter than these examples, which have about 470 to 715 words, and test long
conversations in [part 5](README.md#part-5---test-it).

**Remove everything about documents**: this chatbot has none. In the filled examples, this means
the section **Sources**, the sentences of **Purpose**, **Context** and **Tone and format** that
speak of the documents or of the knowledge base, the help level **Level 2 — Point to the
documents** (`activity-guide` and `project-coach`), and, in **Example**, the lines that cite a
document. The answers then come only from what the model learned: check them on your topic first
([part 5](README.md#part-5---test-it)).

**Short conversations.** With each question, Open WebUI sends the whole conversation again. Start a
**New Chat** for a new topic. What happens beyond 2,048 tokens is not documented: HailoRT, the
Hailo software that hailo-ollama uses to talk to the chip, only writes "Conversation context is
full" as a warning
([HailoRT](https://github.com/hailo-ai/hailort/blob/v5.1.1/hailort/libhailort/src/genai/llm/llm.cpp)).
Measuring it: TO BE COMPLETED.

**One question at a time.** With a group, the others wait. And each participant who takes a turn
makes the HAT read their whole conversation again: hailo-ollama keeps only the last conversation
(read in
[its code](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/src/library/generation_context/generation_context.cpp)).
Group size and waiting times: TO BE COMPLETED. Use it for a demonstration, or with a small group.

---

## Part 6 - Open it to your group

[Part 6](README.md#part-6---open-it-to-your-group) is in the guide. Here are its commands for the
Raspberry Pi.

### Open it to the local network

This is step 1 of [before the first session](README.md#before-the-first-session). Your
administrator account must exist ([part 3](#step-6---create-your-administrator-account)). In the
file of the service, replace `--host 127.0.0.1` (this computer only) with `--host 0.0.0.0` (every
network of the computer), then start Open WebUI again. Its data and accounts are kept, and the
restart signs nobody out:

<!-- ci raspberry-pi,raspberry-pi-hat stage=network expect="--host 0.0.0.0" expect="Open WebUI is ready" check="ss -ltn" expect="0.0.0.0:3000" -->
```bash
sudo sed -i 's/--host 127.0.0.1/--host 0.0.0.0/' /etc/systemd/system/owui-local.service
sudo systemctl daemon-reload && sudo systemctl restart owui-local
grep -o -- '--host [0-9.]*' /etc/systemd/system/owui-local.service
until curl -sf http://localhost:3000/health >/dev/null; do sleep 5; done; echo "Open WebUI is ready"
```

**What you should see.** The third command shows `--host 0.0.0.0`, then, usually within a minute,
`Open WebUI is ready`. Then go back to [the guide](README.md#before-the-first-session), at the end
of step 1: open <http://localhost:3000>.

From now on, Open WebUI starts with the Pi, before anyone signs in, and answers on every network the
Pi joins. If you take the Pi elsewhere, stop it after each session (see [Commands](#commands)), and
start it again before the next one.

With the AI HAT+ 2, check that hailo-ollama is still for this computer only:

<!-- ci raspberry-pi-hat stage=network expect="127.0.0.1:8000" -->
```bash
ss -ltn 'sport = :8000'
```

**What you should see.** A line with `127.0.0.1:8000`. If it shows `0.0.0.0:8000` or `*:8000`, do
[step 4 of the AI HAT+ 2](#step-4---keep-hailo-ollama-on-this-computer) again, then type
`sudo systemctl restart hailo-ollama`.

### Find the address of the computer

Turn off any VPN first, then type:

<!-- ci raspberry-pi,raspberry-pi-hat stage=network expect="src " -->
```bash
ip route get 1.1.1.1 | grep -o 'src [0-9.]*'
```

**What you should see.** `src` and a number, for example `src 192.168.1.20`: this number is the
address of the computer on the network it uses, here the Wi-Fi. This command sends nothing. The
participants open `http://` followed by this number and `:3000`, for example
`http://192.168.1.20:3000`. The address can change after a restart of the computer.

If the phones cannot open it, type `sudo ufw status`. **ufw** is a common firewall of Linux, the
program that decides which connections may enter the computer. If it answers `Status: active`, let
Open WebUI in with `sudo ufw allow 3000/tcp`. If it answers `command not found`, ufw is not
installed. Whether Raspberry Pi OS has another firewall on by default: TO BE COMPLETED (not
tested).

### Keep the Pi running during a session (not tested)

**Power, cooling and supervision.** Keep the Pi on its 27 W supply
([part 1, step 3](#step-3---power-cooling-and-storage-not-tested)), with its Active Cooler, and with
the facilitator: with the AI HAT+ 2, Raspberry Pi asks for adult supervision
([With the AI HAT+ 2](#with-the-ai-hat-2)).

**The first question after a pause (AI HAT+ 2).** hailo-ollama unloads the model 5 minutes after the
last question (read in its code). The next question waits while it loads again: 7.37 seconds for
`qwen2:1.5b` in Hailo's table
([Hailo](https://github.com/hailo-ai/hailo_model_zoo_genai/blob/v5.1.1/docs/MODELS.rst)). A review
of a test version, before the launch, saw "a 25-40 second delay"
([Hackster](https://www.hackster.io/news/gen-ai-on-your-raspberry-pi-a-hands-on-review-of-the-raspberry-pi-ai-hat-2-3c829a8894dd),
blog). Ask one question yourself just before the group arrives.

Whether Raspberry Pi OS puts the Pi to sleep when nobody uses it: TO BE COMPLETED.

---

## Delete Open WebUI and its data

At the end of the project, first keep what you want, your instruction files and your documents
([the participants' data](README.md#the-participants-data)). Then work in the account where Open
WebUI was installed ([part 3](#part-3---start-open-webui)). First check that you are in the right
account:

<!-- ci raspberry-pi,raspberry-pi-hat stage=delete expect="/owui-local/data" -->
```bash
ls -d ~/owui-local/data
```

It must show the folder, for example `/home/anna/owui-local/data`. If it says "No such file or
directory", you are in another account: stop, and change account. If it shows the folder, type:

<!-- ci raspberry-pi,raspberry-pi-hat stage=delete check="test ! -e ~/owui-local && ! systemctl cat owui-local >/dev/null 2>&1 && echo removed" expect="removed" -->
```bash
sudo systemctl disable --now owui-local && sudo rm /etc/systemd/system/owui-local.service
sudo systemctl daemon-reload
rm -rf ~/owui-local
uv cache clean
```

These lines delete Open WebUI, and every account, conversation, memory, feedback, chatbot and
document it holds. `uv cache clean` deletes the copies of the downloads that uv kept (size on a Pi:
TO BE COMPLETED). It also deletes what other projects of the same account put in this cache: they
download it again when they need it. Backups of this computer may still hold copies. The journal of
the computer also keeps the warnings and errors of Open WebUI for a while (no e-mail, no address):
Raspberry Pi OS deletes the oldest messages by itself (not tested).
The models of Ollama hold no data of the participants, nor those of hailo-ollama. uv and its copy
of Python stay: they hold no data either.

### Delete hailo-ollama too

With the AI HAT+ 2, also delete hailo-ollama, its service and the models it downloaded:

<!-- ci raspberry-pi-hat stage=delete check="test ! -e /usr/share/hailo-ollama && test ! -e ~/.hailo/hailort && ! systemctl cat hailo-ollama >/dev/null 2>&1 && echo removed" expect="removed" -->
```bash
sudo systemctl disable --now hailo-ollama && sudo rm /etc/systemd/system/hailo-ollama.service
sudo systemctl daemon-reload
sudo dpkg -r hailo-gen-ai-model-zoo
rm -f ~/hailo_gen_ai_model_zoo_5.1.1_arm64.deb
rm -rf ~/.hailo/hailort ~/hailort.log ~/.config/hailo-ollama ~/.local/share/hailo-ollama
```

`dpkg -r` removes hailo-ollama, its settings file, and the folder `/usr/share/hailo-ollama` with the
downloaded models (we read this in the package, and saw it in a container of a Linux PC). The
fourth line deletes the downloaded package. The last line deletes the log files that the commands
of Hailo, such as `hailortcli` in [step 2](#step-2---install-the-driver-of-the-ai-hat-2-not-tested),
may have written in your home folder (their content: TO BE COMPLETED), and the copies of the
settings and models of hailo-ollama in your home folder, if you ever followed Hailo's own
instructions. The driver of the HAT stays. To remove it too, type `sudo apt remove hailo-h10-all`
(not tested).

---

## Commands

| Command | What it does |
|---|---|
| `sudo systemctl disable --now owui-local` / `sudo systemctl enable --now owui-local` | stops or starts Open WebUI, also after a restart of the computer (its data is kept) |
| `systemctl status owui-local` | shows whether Open WebUI is running (`active (running)`); `q` to quit |
| `sudo journalctl -u owui-local -n 20 --no-pager` | shows the last messages of Open WebUI |
| `cd ~/owui-local && source venv/bin/activate` | activates the virtual environment of Open WebUI, to use `python` or `uv pip` in it |
| `ip route get 1.1.1.1 \| grep -o 'src [0-9.]*'` | shows the address of the computer on the local network |
| `uv self update` | updates uv to its latest version |
| `curl -s http://localhost:8000/api/tags` | lists the models downloaded by hailo-ollama (AI HAT+ 2) |
| `curl -s http://localhost:8000/api/ps` | shows the model loaded on the AI HAT+ 2 |
| `sudo systemctl disable --now hailo-ollama` / `sudo systemctl enable --now hailo-ollama` | stops or starts hailo-ollama (AI HAT+ 2) |
| `systemctl status hailo-ollama` | shows whether hailo-ollama is running; `q` to quit |
| `hailortcli fw-control identify` | shows the AI HAT+ 2 and its firmware |

The commands of Ollama (`ollama pull`, `ollama list`, `ollama ps`) are the same on every system:
see [Commands](README.md#commands) in the guide. hailo-ollama has no `ollama` command: use the lines
above.

---

## Troubleshooting

### "uv: command not found", or "No such file or directory" with `venv/bin/activate`

For uv: type `export PATH="$HOME/.local/bin:$PATH"`, or open a new terminal. For `venv`: type
`cd ~/owui-local` first, or create the virtual environment
([part 3, step 2](#step-2---create-a-virtual-environment)).

### Open WebUI is never ready

Press `Ctrl+C`, then type `sudo journalctl -u owui-local -n 20 --no-pager`: its last lines say what
went wrong. Show them to someone who can read them if you need help. Check also that every step of [part 3](#part-3---start-open-webui) was done by the
same user, in the folder `~/owui-local`: the service uses the paths of this user.

### Open WebUI shows an error with "500" or "Node is NOT a STRING" (AI HAT+ 2)

The chatbot, or the model you chose, sends Open WebUI's tools, and hailo-ollama refuses them
([Hailo forum](https://community.hailo.ai/t/hailo-ollama-return-type-unsuitable-for-open-webui/19327)).
Set **Function Calling** to **Legacy** and switch off **Builtin Tools**: on the model, as in
[step 9](#step-9---set-the-model-of-the-ai-hat-2-not-tested), and on each chatbot, as in
[step 10](#step-10---build-chatbots-for-the-ai-hat-2-not-tested). Then reload the page, and ask
again. In our test on 29 October 2026 (Open WebUI 0.12.4 on a Linux PC, with the small program that
stands in for hailo-ollama, not the HAT), Open WebUI answered "Open WebUI: Server Connection Error"
through its programming interface; the text in the browser: TO BE COMPLETED.

### The answer stops in the middle, or is empty (AI HAT+ 2)

The conversation, with the instructions, may be near or above 2,048 tokens. Start a **New Chat**,
and shorten the instructions ([step 10](#step-10---build-chatbots-for-the-ai-hat-2-not-tested)).
Not measured: TO BE COMPLETED.

### The first answer is slow after a pause (AI HAT+ 2)

hailo-ollama loads the model again after 5 minutes without a question: see
[Keep the Pi running during a session](#keep-the-pi-running-during-a-session-not-tested).

### qwen2:1.5b is missing from the list of models (AI HAT+ 2)

Open WebUI lists only the models that hailo-ollama has already downloaded. Type
`curl -s http://localhost:8000/api/tags`. If the list is empty (`{"models":[]}`), do
[step 7](#step-7---download-a-model-for-the-ai-hat-2-not-tested). If `qwen2:1.5b` is there, check the address
of [step 8](#step-8---connect-open-webui-to-hailo-ollama-not-tested): `http://127.0.0.1:8000`.

### hailo-ollama does not start (AI HAT+ 2)

Type `sudo journalctl -u hailo-ollama -n 20 --no-pager`: it says whether the service started,
stopped or failed. The messages of hailo-ollama itself are not there (`StandardOutput=null`,
[step 5](#step-5---start-hailo-ollama-as-a-service-not-tested)). To see them once, without the group, stop the
service and start hailo-ollama by hand, as in Raspberry Pi's documentation
([Raspberry Pi](https://www.raspberrypi.com/documentation/computers/ai.html)):

```bash
sudo systemctl stop hailo-ollama
XDG_CONFIG_HOME=/etc/xdg XDG_DATA_HOME=/usr/share HAILORT_LOGGER_PATH=NONE hailo-ollama
```

The second line starts hailo-ollama with the same settings as the service (step 5), but in this
terminal. hailo-ollama shows its messages there, and it listens at the address of its settings
file ([step 4](#step-4---keep-hailo-ollama-on-this-computer)). Every question sent to it then
appears there, so do it without the group. Press `Ctrl+C` to stop it, then type
`sudo systemctl start hailo-ollama`.

For the other problems, see [Troubleshooting](README.md#troubleshooting) in the guide.
