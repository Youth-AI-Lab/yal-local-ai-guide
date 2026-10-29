# Linux: install the chatbot on your computer

This page is part of the guide [A chatbot that runs on your own computer](README.md). It holds what
depends on the system of the computer, here **Linux**: parts 1 to 3, the commands of part 6, the
deletion at the end of the project, and the commands and troubleshooting of Linux. We tested it on
Ubuntu 26.04, with an NVIDIA graphics card.

Do parts 1 to 3 on this page. Then go back to the guide for
[part 4](README.md#part-4---build-the-chatbot), [part 5](README.md#part-5---test-it) and
[part 6](README.md#part-6---open-it-to-your-group). When part 6 needs a command, it sends you back
to this page. The words *terminal*, `sudo`, *driver*, *service* and *port* are explained in the
[prerequisites](README.md#prerequisites) of the guide.

Another system: [macOS](macos.md), [Windows](windows.md), [Raspberry Pi](raspberry-pi.md).

> [!WARNING]
> **A technical part.** Parts 1 to 3 use commands typed in a terminal, some with the administrator
> rights of the computer (`sudo`), and they change its settings. Do them only if you feel confident
> with this.

---

## Part 1 - Check the computer

The speed of a local chatbot depends first on one thing: whether the model runs on a **graphics
card**. On the processor alone, our laptop took one to two minutes per answer.
Do this part before part 2.

### Step 1 - Look for a graphics card

Open a terminal (on Ubuntu: press `Ctrl+Alt+T`) and type:

```bash
lspci | grep -iE "vga|3d|display"
```

**What you should see.** One line per graphics chip. On our laptop, two lines: an **Intel** chip,
which is part of the processor, and an **NVIDIA** card.

```
00:02.0 VGA compatible controller: Intel Corporation Arrow Lake-P [Intel Graphics] (rev 03)
01:00.0 VGA compatible controller: NVIDIA Corporation GB207GLM [RTX PRO 500 Blackwell Generation Laptop GPU] (rev a1)
```

- **An NVIDIA card**: go to step 2.
- **Only an Intel or AMD chip in the processor**: Ollama will most likely run on the processor, as
  on our laptop before step 2 (one to two minutes per answer). Ollama's documentation describes
  extra steps for some of these chips (Vulkan). We did not test them.

### Step 2 - Check that the card works

```bash
nvidia-smi
```

**What you should see.** A table with the name of the card and its memory, for example
`NVIDIA RTX PRO 500 Black...` and `11MiB / 6113MiB`. The second number is the memory of the card.
We measured with a **6 GB** card, and the models of this guide already overflow it a little
([part 2](#step-4---download-the-model)). We did not test a smaller card: Ollama would then run a
bigger part of the model on the processor, and the answers would be slower.

If `nvidia-smi` answers **"command not found"**, no NVIDIA driver is installed yet: the computer
uses a basic built-in driver.

If `nvidia-smi` answers **"No devices found"**, a driver is installed but does not work with the
card. This happened on our laptop. Its card is of the **Blackwell** generation, and NVIDIA writes
that "Blackwell and later are only supported by the open kernel modules"
([NVIDIA](https://download.nvidia.com/XFree86/Linux-x86_64/580.95.05/README/kernel_open.html)).
The messages of the computer said so too:

```bash
sudo dmesg | grep -i "open kernel modules"
```

If it answers **"couldn't communicate with the NVIDIA driver"**, a driver is installed but not
loaded: do the steps below, and read step 3 carefully.

In each of these cases:

1. List the drivers Ubuntu offers: `sudo ubuntu-drivers list`
2. Install the driver it lists. For a recent card, choose the version whose name ends with
   **`-open`**: on Ubuntu, these packages use the open modules. On our laptop, it was
   `sudo apt install nvidia-driver-595-open`
3. During the installation, the terminal may ask you to choose a password for **Secure Boot**:
   choose one and write it down. Restart the computer. If a blue screen **Perform MOK management**
   appears, choose **Enroll MOK** → **Continue** → **Yes**, type this password, then **Reboot**. If
   you skip this screen, the driver does not load.
4. Type `nvidia-smi` again: the card and its memory appear.

> [!WARNING]
> Changing the graphics driver can stop the display of a computer. It is the most delicate step of
> this guide: do it only if you feel confident, at a time when the computer is not needed.

---

## Part 2 - Install Ollama and a model

*A technical part, after part 1.* Finish part 1 first. If `nvidia-smi` is missing, Ollama's
installer installs NVIDIA drivers of its own, which may not be the ones your card needs. If
`nvidia-smi` is there, the installer says "NVIDIA GPU installed." even when the card does not work:
only `nvidia-smi` (part 1) and `ollama ps` ([step 4](#step-4---download-the-model)) tell you.

### Step 1 - Install Ollama

Ubuntu does not always come with `curl`, the tool that the commands of this page use to download.
Install it first:

<!-- ci linux stage=install check="curl --version" expect="libcurl/" -->
```bash
sudo apt update && sudo apt install -y curl
```

**What you should see.** `curl --version` answers with a version number.

On Linux, the official installation of Ollama is one line ([Ollama](https://docs.ollama.com/linux)):

<!-- ci linux stage=install check="ollama --version" expect="version" -->
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

It installs Ollama as a service that starts with the computer.

**What you should see.** `ollama --version` answers with a version number. We tested 0.40.8; on
29 October 2026, this line installed 0.40.13 on the machines of GitHub, and the next steps showed
the same. If
`ollama --version` answers "command not found", the download failed: check `curl --version`, then
type the line again.

### Step 2 - Keep Ollama on this computer

Ollama also offers **cloud models**, which run on Ollama's servers, not on your computer. Turn this
off, so that no question can leave by mistake
([Ollama](https://docs.ollama.com/faq#how-do-i-disable-ollama-cloud-features)):

<!-- ci linux stage=install -->
```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_NO_CLOUD=1"\n' | sudo tee /etc/systemd/system/ollama.service.d/no-cloud.conf
sudo systemctl daemon-reload && sudo systemctl restart ollama
```

The second command writes a small settings file for the Ollama service, and shows its two lines.
The third one starts Ollama again with this setting.

**What you should see.** Check the setting, then what Ollama says about it:

<!-- ci linux stage=install expect="OLLAMA_NO_CLOUD=1" expect="Ollama cloud disabled: true" -->
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

| Model | Download | Licence | What we saw |
|---|---|---|---|
| `qwen2.5:7b` | 4.7 GB | Apache 2.0 (all sizes of Qwen2.5 except 3B and 72B, [Ollama](https://ollama.com/library/qwen2.5)) | 13 to 15 / 22 with documents |
| `mistral:7b` | 4.4 GB | Apache 2.0 ([Ollama](https://ollama.com/library/mistral)) | 13 to 15 / 22 with documents |
| `phi3.5` | — | MIT ([model card](https://huggingface.co/microsoft/Phi-3.5-mini-instruct)) | broken words: not for young people |

The Apache 2.0 and MIT licences allow the use by an association, and they have no rule on minors.
Other families of models have their own licences and use policies: read them first. For example,
the [Llama 3.1 policy](https://www.llama.com/llama3_1/use-policy/) has rules about minors, and the
[Gemma terms](https://ai.google.dev/gemma/terms) let Google restrict, even remotely, any use it
reasonably believes breaks those terms. We did not measure these models.

### Step 4 - Download the model

<!-- ci linux stage=install -->
```bash
ollama pull qwen2.5:7b
```

Then check that it runs, and where:

<!-- ci linux stage=install expect="PROCESSOR" -->
```bash
ollama run qwen2.5:7b "Hello" && ollama ps
```

**What you should see.** An answer, then a line for the model with a column **PROCESSOR**:

- **`100% GPU`**: the model is on the graphics card;
- **`100% CPU`**: the model is on the processor, which is slow. Go back to
  [part 1](#part-1---check-the-computer);
- a split such as `13%/87% CPU/GPU`: the model does not fit entirely on the card. This is what we
  saw on our 6 GB card once the chatbot was set up
  ([part 4](README.md#part-4---build-the-chatbot)), and it was still fast.

---

## Part 3 - Start Open WebUI

*A technical part.* Open WebUI is a Python program. You install it in a folder of its own,
`~/owui-local`, and the computer runs it as a service, on the same computer as Ollama. In this
part, only this computer can open it. You open it to your local network in
[part 6](README.md#part-6---open-it-to-your-group), when your administrator account exists.

### Step 1 - Install uv

**uv** is a free tool that installs Python programs, and the version of Python they need. Open
WebUI 0.12.4 needs Python 3.11 or 3.12. Ubuntu 26.04 comes with Python 3.14, which is too new: uv
downloads Python 3.12 for Open WebUI, without changing the Python of the computer.

Do this whole part in a normal account of the computer, the one you will use for Open WebUI, not
as `root`: `whoami` must not answer `root`. Open WebUI will run with the rights of this account.

<!-- ci linux stage=install check="uv --version" expect="uv 0.13.6" -->
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

<!-- ci linux stage=install check="python --version" expect="Python 3.12" -->
```bash
mkdir -p ~/owui-local && chmod 700 ~/owui-local && cd ~/owui-local
uv venv --managed-python --python 3.12 venv
source venv/bin/activate
```

`chmod 700` lets only your account open this folder: it will hold the conversations of your group.
The second command downloads Python 3.12 (about 40 MB) the first time; `--managed-python` makes uv
use its own copy, the one we tested, even if the computer already has a Python 3.12. The third one
**activates** the virtual environment: in this terminal, `python` and the programs you install now
are those of `venv`.

**What you should see.** `(venv)` at the start of the line where you type. If you close the
terminal before the end of this part, open a new one and type
`cd ~/owui-local && source venv/bin/activate` before you go on.

### Step 3 - Install Open WebUI

<!-- ci linux stage=install check="uv pip show open-webui" expect="Version: 0.12.4" -->
```bash
uv pip install --torch-backend cpu "torch<=2.9.1" open-webui==0.12.4
```

This installs Open WebUI 0.12.4 in `venv`, with the programs it needs. On our laptop, it was about
830 MB to download, 2.4 GB once on the disk, and it took 40 seconds. We measured the answers with an
earlier version, 0.11.4 ([About](README.md#about)). Open WebUI uses **torch** to search in your
documents.
`--torch-backend cpu` installs the version of torch for the processor: the graphics card
is for Ollama, and the version for the card is a much bigger download. `torch<=2.9.1` is the
version in Open WebUI's own installation, the one we measured.

Then download the small model that Open WebUI uses to search in your documents (about 90 MB, 30
seconds on our laptop). With the settings of this guide, Open WebUI never downloads anything by
itself, so it needs it now:

<!-- ci linux stage=install -->
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

<!-- ci linux stage=install -->
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

<!-- ci linux stage=install -->
```bash
sudo tee /etc/systemd/system/owui-local.service >/dev/null <<EOF
[Unit]
Description=Open WebUI for the group
After=network-online.target ollama.service
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

First check that no other program uses port 3000: type `ss -ltn 'sport = :3000'`. It must show only
one line, the titles. If a second line shows `:3000`, another program uses this port, maybe another
Open WebUI: stop it first. Otherwise the next block could say "Open WebUI is ready" for this other
program.

Then start Open WebUI, and wait until it is ready:

<!-- ci linux stage=install expect="Open WebUI is ready" check="ss -ltn" expect="127.0.0.1:3000" -->
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now owui-local
until curl -sf http://localhost:3000/health >/dev/null; do sleep 5; done; echo "Open WebUI is ready"
```

**What you should see.** `Open WebUI is ready`, usually within a minute (22 seconds on our laptop,
for the first start, which prepares its database).
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
`qwen2.5:7b` (Open WebUI may have chosen another model of Ollama for you). Ask "Hello, who are
you?": the first answer is slower, while the model loads. On our laptop, it came after 10 seconds,
5 of them to load the model. If the list is empty, see
[Troubleshooting](README.md#the-model-list-is-empty). If the answer is "does not support tools", see
[this entry](README.md#the-answer-is-does-not-support-tools).

---

## Part 6 - Open it to your group

[Part 6](README.md#part-6---open-it-to-your-group) is in the guide. Here are its commands for Linux.

### Open it to the local network

This is step 1 of [before the first session](README.md#before-the-first-session). Your
administrator account must exist ([part 3](#step-6---create-your-administrator-account)). In the
file of the service, replace `--host 127.0.0.1` (this computer only) with `--host 0.0.0.0` (every
network of the computer), then start Open WebUI again. Its data and accounts are kept, and the
restart signs nobody out:

<!-- ci linux stage=network expect="--host 0.0.0.0" expect="Open WebUI is ready" check="ss -ltn" expect="0.0.0.0:3000" -->
```bash
sudo sed -i 's/--host 127.0.0.1/--host 0.0.0.0/' /etc/systemd/system/owui-local.service
sudo systemctl daemon-reload && sudo systemctl restart owui-local
grep -o -- '--host [0-9.]*' /etc/systemd/system/owui-local.service
until curl -sf http://localhost:3000/health >/dev/null; do sleep 5; done; echo "Open WebUI is ready"
```

**What you should see.** The third command shows `--host 0.0.0.0`, then, usually within a minute,
`Open WebUI is ready`. Then go back to [the guide](README.md#before-the-first-session), at the end
of step 1: open <http://localhost:3000>.

From now on, Open WebUI starts with the computer, before anyone signs in, and answers on every
network the computer joins, also at home or in a café. On a laptop, stop it after each session (see
[Commands](#commands)), and start it again before the next one.

### Find the address of the computer

Turn off any VPN first, then type:

<!-- ci linux stage=network expect="src " -->
```bash
ip route get 1.1.1.1 | grep -o 'src [0-9.]*'
```

**What you should see.** `src` and a number, for example `src 192.168.1.20`: this number is the
address of the computer on the network it uses, here the Wi-Fi. This command sends nothing. The
participants open `http://` followed by this number and `:3000`, for example
`http://192.168.1.20:3000`. The address can change after a restart of the computer.

If the phones cannot open it, type `sudo ufw status`. If it answers `Status: active`, the firewall
of Ubuntu is on: let Open WebUI in with `sudo ufw allow 3000/tcp`.

---

## Delete Open WebUI and its data

At the end of the project, first keep what you want, your instruction files and your documents
([the participants' data](README.md#the-participants-data)). Then work in the account where Open
WebUI was installed ([part 3](#part-3---start-open-webui)). First check that you are in the right
account:

<!-- ci linux stage=delete expect="/owui-local/data" -->
```bash
ls -d ~/owui-local/data
```

It must show the folder, for example `/home/anna/owui-local/data`. If it says "No such file or
directory", you are in another account: stop, and change account. If it shows the folder, type:

<!-- ci linux stage=delete check="test ! -e ~/owui-local && ! systemctl cat owui-local >/dev/null 2>&1 && echo removed" expect="removed" -->
```bash
sudo systemctl disable --now owui-local && sudo rm /etc/systemd/system/owui-local.service
sudo systemctl daemon-reload
rm -rf ~/owui-local
uv cache clean
```

These lines delete Open WebUI, and every account, conversation, memory, feedback, chatbot and
document it holds. `uv cache clean` deletes the copies of the downloads that uv kept (about 2.7 GB
with Open WebUI 0.11.4; TO BE COMPLETED for 0.12.4). It also deletes what other projects of the same
account put in this cache: they download it again when they need it. Backups of this computer may
still hold copies. The journal of the computer also keeps the warnings and errors of Open WebUI for
a while (no e-mail, no address): Ubuntu deletes the oldest messages by itself.
The models of Ollama hold no data of the participants. uv and its copy of Python stay: they hold
no data either.

---

## Commands

| Command | What it does |
|---|---|
| `nvidia-smi` | shows the NVIDIA card and its memory |
| `sudo systemctl disable --now owui-local` / `sudo systemctl enable --now owui-local` | stops or starts Open WebUI, also after a restart of the computer (its data is kept) |
| `systemctl status owui-local` | shows whether Open WebUI is running (`active (running)`); `q` to quit |
| `sudo journalctl -u owui-local -n 20 --no-pager` | shows the last messages of Open WebUI |
| `cd ~/owui-local && source venv/bin/activate` | activates the virtual environment of Open WebUI, to use `python` or `uv pip` in it |
| `ip route get 1.1.1.1 \| grep -o 'src [0-9.]*'` | shows the address of the computer on the local network |
| `uv self update` | updates uv to its latest version |

The commands of Ollama (`ollama pull`, `ollama list`, `ollama ps`) are the same on every system:
see [Commands](README.md#commands) in the guide.

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

For the other problems, see [Troubleshooting](README.md#troubleshooting) in the guide.
