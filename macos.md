# macOS: install the chatbot on your computer

This page is part of the guide [A chatbot that runs on your own computer](README.md). It holds what
depends on the system of the computer, here **macOS**: parts 1 to 3, the commands of part 6, the
deletion at the end of the project, and the commands and troubleshooting of macOS. It is for a Mac
with an **Apple chip** (M1 or newer) and **macOS 15 Sequoia or newer**
([part 1](#part-1---check-the-computer) says why).

Do parts 1 to 3 on this page. Then go back to the guide for
[part 4](README.md#part-4---build-the-chatbot), [part 5](README.md#part-5---test-it) and
[part 6](README.md#part-6---open-it-to-your-group). When part 6 needs a command, it sends you back
to this page. The words *terminal*, `sudo`, *driver*, *service* and *port* are explained in the
[prerequisites](README.md#prerequisites) of the guide.

Another system: [Linux](linux.md), [Windows](windows.md), [Raspberry Pi](raspberry-pi.md).

> [!WARNING]
> **A technical part.** Parts 1 to 3 use commands typed in a terminal, some with the administrator
> rights of the computer (`sudo`), and they change its settings. Do them only if you feel confident
> with this.

> [!NOTE]
> **Not tested on a real Mac.** We measured the guide on Linux only. The commands of this page come
> from the documentation of Apple, Homebrew, Ollama and uv, and from the code of Ollama. A machine
> of GitHub (macOS 26, Apple chip, nobody in front of the screen) followed parts 2, 3 and 6 and the
> deletion from start to end on 29 October 2026 ([`ci/README.md`](ci/README.md)). TO BE
> COMPLETED: a run on a real Mac, with its windows, and a group.

**The terminal of a Mac** is the app **Terminal**: press `Cmd+Space`, type `Terminal`, and press
`Enter`. When a command starts with `sudo`, the terminal asks for the password of your account on
the Mac. Nothing appears while you type it: this is normal. Press `Enter` at the end.

This page gives the names of macOS in English. On a Mac in another language they are translated:
for example, **System Settings** reads **Réglages Système** in French.

---

## Part 1 - Check the computer

The speed of a local chatbot depends first on one thing: whether the model runs on the **graphics**
of the computer. On a Mac with an Apple chip, the graphics are part of the chip, and Ollama uses
them ([Ollama](https://docs.ollama.com/gpu)). Do this part before part 2.

### Step 1 - Check the chip and the version of macOS

Open a terminal and type:

<!-- ci macos stage=install expect="arm64" -->
```bash
uname -m
sw_vers -productVersion
```

**What you should see.** Two lines: `arm64`, then the version of macOS, for example `15.6`. The
first number must be **15 or more**.

- **`x86_64`** instead of `arm64`: this Mac has an Intel processor. This page is not for it: the
  version of torch that Open WebUI uses (part 3) does not exist for it, and Ollama would run on the
  processor only ([Ollama](https://docs.ollama.com/macos)).
- **A version lower than 15**: update macOS first (Apple menu → **System Settings** → **General** →
  **Software Update**). This page installs programs with Homebrew, which supports macOS 15 Sequoia
  and newer ([Homebrew](https://docs.brew.sh/Installation)).

### Step 2 - Check the memory

Click the Apple menu at the top left of the screen → **About This Mac**. The line **Memory** gives
the memory of the Mac, for example `16 GB`. On an Apple chip, the processor and the graphics share
this memory: the model and every open program use the same memory. A model of this guide is a
download of 4.4 to 4.7 GB ([part 2](#step-3---choose-a-model-and-read-its-licence)). On our Linux
laptop, `qwen2.5:7b` with the context of part 4 (8192) did not fit in 6 GB of graphics memory: 13%
of it ran on the processor. TO BE COMPLETED: how much memory a Mac needs for these models, and how
fast it answers. We did not measure a Mac.

There is no graphics driver to install on a Mac: macOS has it already. You check where the model
runs in [part 2, step 4](#step-4---download-the-model).

### Step 3 - Check for Homebrew, or install it

**Homebrew** is a free tool that installs programs on a Mac, with one command each. Part 2 and part
3 use it.

**Your account must be an administrator of the Mac.** Apple menu → **System Settings** → **Users &
Groups**: your name must show **Admin** (not tested). Without it, `sudo` and the installer of
Homebrew refuse to work. Do parts 1 to 3 in this account, the one you will use for Open WebUI.
Homebrew belongs to the account that installed it: if `brew install` later says "Permission
denied", another account of this Mac installed Homebrew, so ask that person for help.

First, check whether Homebrew is already there:

<!-- ci macos stage=install expect="Homebrew" -->
```bash
brew --version
```

**What you should see.** A line that starts with `Homebrew` and a number: Homebrew is there. Go to
the end of this step.

If the answer is `command not found: brew`, install Homebrew with the command of its website
([brew.sh](https://brew.sh)):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

The installer first asks for your password, then says what it will install, and waits: press
`Enter` when it says "Press RETURN/ENTER to continue". It may also install Apple's **Command Line
Tools for Xcode**, which takes a few minutes. If a window of Apple asks to install them, click
**Install**; when they are installed, press a key in the terminal, as it asks ("Press any key when
the installation has completed"). Wait until it says `Installation successful!`. (not tested)

At the end, under **Next steps**, it shows commands that let the terminal find `brew`. On a Mac
with an Apple chip, in the Terminal app, they are these three lines. Copy them all, and press
`Enter`:

```bash
echo >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv zsh)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv zsh)"
```

Then type `brew --version` again: it answers `Homebrew` and a number.

**In both cases**, turn off the anonymous statistics that Homebrew sends about what it installs:

<!-- ci macos stage=install -->
```bash
brew analytics off
```

---

## Part 2 - Install Ollama and a model

*A technical part, after part 1.*

### Step 1 - Install Ollama

Ollama makes an app for the Mac. Homebrew installs it under the name `ollama-app`. This entry of
Homebrew is maintained by Homebrew, not by Ollama: it downloads Ollama's official app from Ollama's
own page on GitHub, and puts it in **Applications** (see
[Homebrew's page for it](https://formulae.brew.sh/cask/ollama-app)).

<!-- ci macos stage=install check="ollama --version" expect="version" -->
```bash
brew install --cask ollama-app
```

If Ollama is already on this Mac, Homebrew says that an app is already there: keep it, and go on.

Then create the link that the Ollama app looks for, the first time it starts, so that its command
`ollama` works in every terminal. Ollama's own installer creates the same link. Without it, Ollama
asks for your password in a window at its first start:

<!-- ci macos stage=install -->
```bash
sudo mkdir -p /usr/local/bin
sudo ln -sf /Applications/Ollama.app/Contents/Resources/ollama /usr/local/bin/ollama
```

**What you should see.** Type `ollama --version`: it answers with a version number. It may also
say that it cannot connect to a running Ollama: this is normal, Ollama is not started yet.

### Step 2 - Keep Ollama on this computer

Ollama also offers **cloud models**, which run on Ollama's servers, not on your computer. Turn this
off before Ollama starts for the first time, so that no question can leave by mistake. Ollama reads
this setting from a small file in its folder, `~/.ollama/server.json`
([Ollama](https://docs.ollama.com/faq#how-do-i-disable-ollama-cloud-features)):

<!-- ci macos stage=install -->
```bash
mkdir -p ~/.ollama
echo '{"disable_ollama_cloud": true}' > ~/.ollama/server.json
```

If Ollama is already running (its icon, a llama, is in the menu bar at the top right of the
screen), click this icon → **Quit Ollama** first. Then start it, and wait until it is ready:

<!-- ci macos stage=install expect="Ollama is ready" -->
```bash
open /Applications/Ollama.app --args hidden
until ollama list >/dev/null 2>&1; do sleep 2; done; echo "Ollama is ready"
```

The first line starts Ollama without opening its window, as Ollama's own installer does: its icon
appears in the menu bar. It names the app by its place in **Applications**: just after an
installation, macOS may not know the app by its name yet. The Ollama app also starts by itself each time you sign in on the Mac
([Ollama](https://docs.ollama.com/faq#how-can-i-stop-ollama-from-starting-when-i-login-to-my-computer)).
The second line waits until Ollama answers.

The first time, macOS may ask whether you want to open Ollama, an app downloaded from the internet:
click **Open**. (not tested)

**What you should see.** `Ollama is ready`. Then check what Ollama says about the cloud:

<!-- ci macos stage=install expect="Ollama cloud disabled: true" -->
```bash
grep "cloud disabled" ~/.ollama/logs/server.log
```

It shows a line with `Ollama cloud disabled: true`. If not, quit Ollama (icon → **Quit Ollama**),
type the two commands of the first box of this step again, then the two of the second box. You can
also check in Ollama's window: icon → **Settings**. The switch **Cloud** ("Enable cloud models and
web search.") must be off.

In the same **Settings**, leave **Expose Ollama to the network** off. Ollama has no accounts. If it
were opened to the network, anyone on your Wi-Fi could use the model directly, without the rules of
your chatbot. Only Open WebUI is for the participants.

> [!NOTE]
> The Ollama app updates itself: when its menu offers to restart to update, do it after a session,
> not during one ([Ollama](https://docs.ollama.com/faq#how-can-i-upgrade-ollama)).

### Step 3 - Choose a model and read its licence

A model is a large file that you download once. Its **licence** says what you may do with it: read
it before you use a model with a group. Use only models without `cloud` in their name.

| Model | Download | Licence | What we saw (on Linux) |
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

<!-- ci macos stage=install -->
```bash
ollama pull qwen2.5:7b
```

Then check that it runs, and where:

<!-- ci macos stage=install expect="PROCESSOR" -->
```bash
ollama run qwen2.5:7b "Hello" && ollama ps
```

**What you should see.** An answer, then a line for the model with a column **PROCESSOR**:

- **`100% GPU`**: the model is on the graphics of the chip;
- **`100% CPU`**: the model is on the processor, which is slow. Check
  [part 1](#part-1---check-the-computer): this happens on a Mac with an Intel processor;
- a split such as `48%/52% CPU/GPU`: the model does not fit entirely in the memory that Ollama
  gives to the graphics ([Ollama](https://docs.ollama.com/gpu)). TO BE COMPLETED: what we see on a
  Mac.

---

## Part 3 - Start Open WebUI

*A technical part.* Open WebUI is a Python program. You install it in a folder of its own,
`~/owui-local`, and the Mac runs it as a service of your account, on the same computer as Ollama.
In this part, only this computer can open it. You open it to your local network in
[part 6](README.md#part-6---open-it-to-your-group), when your administrator account exists.

### Step 1 - Install uv

**uv** is a free tool that installs Python programs, and the version of Python they need. Open
WebUI 0.12.4 needs Python 3.11 or 3.12: uv downloads Python 3.12 for Open WebUI, without changing
anything else on the Mac.

Do this whole part in your normal account on the Mac, the one you will use for Open WebUI. Open
WebUI will run with the rights of this account.

<!-- ci macos stage=install check="uv --version" expect="uv 0." -->
```bash
brew install uv
```

**What you should see.** Type `uv --version`: it answers a line that starts with `uv` and a
number, **0.13.4 or newer**. Homebrew installs the latest version it has: 0.13.4 on the Mac of
GitHub on 29 October 2026. Older versions have a security problem
([GHSA-hq85-5cpj-mr62](https://github.com/astral-sh/uv/security/advisories/GHSA-hq85-5cpj-mr62)):
if you see one, type `brew upgrade uv`.

### Step 2 - Create a virtual environment

A **virtual environment** (often called a *venv*) is a folder that holds the programs installed for
one project, apart from the rest of the computer. It uses the Python that uv downloaded. Deleting
the folder deletes these programs. Create the folder of Open WebUI, and its virtual environment
inside, named `venv`:

<!-- ci macos stage=install check="python --version" expect="Python 3.12" -->
```bash
mkdir -p ~/owui-local && chmod 700 ~/owui-local && cd ~/owui-local
uv venv --managed-python --python 3.12 venv
source venv/bin/activate
```

`chmod 700` lets only your account open this folder: it will hold the conversations of your group.
The second command downloads Python 3.12 (about 25 MB on the Mac of GitHub) the first time;
`--managed-python` makes uv use its own copy, even if the Mac already has a Python 3.12. The third
one **activates** the virtual environment: in this terminal, `python` and the programs you install
now are those of `venv`.

**What you should see.** `(venv)` at the start of the line where you type. If you close the
terminal before the end of this part, open a new one and type
`cd ~/owui-local && source venv/bin/activate` before you go on.

### Step 3 - Install Open WebUI

<!-- ci macos stage=install check="uv pip show open-webui" expect="Version: 0.12.4" -->
```bash
uv pip install --torch-backend cpu "torch<=2.9.1" open-webui==0.12.4
```

This installs Open WebUI 0.12.4 in `venv`, with the programs it needs: the same command as on Linux.
On our Linux laptop, it was about 830 MB to download, 2.4 GB once on the disk, and it took 40
seconds. TO BE COMPLETED: these figures on a Mac. Open WebUI uses **torch** to search in your
documents. `--torch-backend cpu` takes torch from PyTorch's own website, as on Linux. On a Mac, this
torch can also use the graphics of the chip, and Open WebUI uses them to search in your documents:
Ollama and Open WebUI share the graphics. TO BE COMPLETED: whether this slows the answers.
`torch<=2.9.1` is the version in Open WebUI's own installation, the one we measured. The Mac of
GitHub installed every program of this command.

Then download the small model that Open WebUI uses to search in your documents (about 90 MB). With
the settings of this guide, Open WebUI never downloads anything by itself, so it needs it now:

<!-- ci macos stage=install -->
```bash
SENTENCE_TRANSFORMERS_HOME=$HOME/owui-local/data/cache/embedding/models python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

**What you should see.** Type `uv pip show open-webui`: it shows `Version: 0.12.4`. The download
of the search model may show a warning about "unauthenticated requests" and a "LOAD REPORT" with the
word `UNEXPECTED`: they are normal. It must not end with `Error`.

### Step 4 - Get the settings for a group

The file [`openwebui.env`](openwebui.env) of this guide holds the settings we use with young
people:

- Open WebUI is set not to send anything out by itself (no statistics, no update checks, no web
  search);
- the participants do not see the buttons to change a chatbot, or to upload files or photos. This
  hides the buttons; it is not a lock: a participant with technical skills could still send a file;
- a banner asks them not to write personal information;
- a sign-in lasts 12 hours, and the participants do not see your name and e-mail;
- Open WebUI writes only warnings and errors in its log, not the e-mail used at each sign-in or the
  address of each phone.

Each line of the file is explained. On Linux, the service of the computer reads this file itself.
The services of macOS cannot, so a small program of this guide, [`owui-start.py`](owui-start.py),
does it: it reads `openwebui.env`, starts Open WebUI with these settings, and writes what Open WebUI
says in its log, the file `~/owui-local/open-webui.log`. Download both files into the folder of
Open WebUI:

<!-- ci macos stage=install -->
```bash
cd ~/owui-local
curl -fsSLO https://raw.githubusercontent.com/Youth-AI-Lab/yal-local-ai-guide/main/openwebui.env
curl -fsSLO https://raw.githubusercontent.com/Youth-AI-Lab/yal-local-ai-guide/main/owui-start.py
```

Open WebUI saves most of these settings in its own data at its very first start. After that,
changing the file has no effect on them: you change them in the **Admin Panel**. For example, to
show the banner in the language of your group, change its text after
[step 6](#step-6---create-your-administrator-account), in **Admin Panel** → **Settings** →
**General**, in the part about banners ("Create announcements shown to users in the app."), then
click **Save**.

### Step 5 - Start Open WebUI as a service

On a Mac, a program that runs by itself for your account is a **launch agent**: a small file in
the folder `~/Library/LaunchAgents` tells macOS what to start. Copy this whole block into the
terminal, from `mkdir` to the second `EOF`, and press `Enter`. It writes this file, with the paths
of your folder:

<!-- ci macos stage=install check="plutil -lint ~/Library/LaunchAgents/org.youthailab.owui-local.plist" expect=": OK" -->
```bash
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/org.youthailab.owui-local.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>org.youthailab.owui-local</string>
  <key>ProgramArguments</key>
  <array>
    <string>$HOME/owui-local/venv/bin/python</string>
    <string>$HOME/owui-local/owui-start.py</string>
    <string>127.0.0.1</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$HOME/owui-local</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <dict>
    <key>SuccessfulExit</key>
    <false/>
  </dict>
</dict>
</plist>
EOF
```

Then type `plutil -lint ~/Library/LaunchAgents/org.youthailab.owui-local.plist`: it ends with
`OK`, which means that macOS can read the file.

This launch agent:

- starts Open WebUI on **port 3000** of this computer, for this computer only (`127.0.0.1`), with
  the settings of `openwebui.env`;
- keeps its data (accounts, chatbots, conversations, documents) in the folder
  `~/owui-local/data`;
- starts it again each time you sign in on the Mac, and if it stops by accident.

macOS may give a launch agent less of the processor than an app (it says it applies "light resource
limits" to such a program). TO BE COMPLETED: whether this makes Open WebUI slower on a Mac.

It runs only while you are signed in on the Mac. After a restart of the Mac, sign in to your
account: Open WebUI starts then.

Then start it, and wait until it is ready:

<!-- ci macos stage=install expect="Open WebUI is ready" check="lsof -nP -iTCP:3000 -sTCP:LISTEN" expect="127.0.0.1:3000" -->
```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/org.youthailab.owui-local.plist
until curl -sf http://localhost:3000/health >/dev/null; do sleep 5; done; echo "Open WebUI is ready"
```

**What you should see.** `Open WebUI is ready`, usually within a minute (22 seconds on our Linux
laptop; TO BE COMPLETED: the first start on a Mac, which prepares its database). Then type
`lsof -nP -iTCP:3000 -sTCP:LISTEN`: its line ends with `127.0.0.1:3000 (LISTEN)`, this computer
only. macOS may also show a notification about a new item that runs in the background: this is
Open WebUI. Leave it allowed. (not tested)

If nothing appears after 5 minutes, press `Ctrl+C` and type `tail -n 20 ~/owui-local/open-webui.log`.
A line with "address already in use" means that another program of the computer uses port 3000:
stop this program first.

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
**Okay, Let's Go!** at the bottom (the participants never see it). Then the chat page of Open
WebUI. Your name at the bottom left opens a menu with **Admin Panel**: you are the administrator.
**The first account becomes the administrator**, and Open WebUI then **closes the sign-ups** by
itself. Nobody else can create an account until you open them in
[part 6](README.md#part-6---open-it-to-your-group).

### Step 7 - Check the connection to Ollama

Click **New Chat**. In the list of models, at the bottom right of the message box, choose
`qwen2.5:7b` (Open WebUI may have chosen another model of Ollama for you). Ask "Hello, who are
you?": the first answer is slower, while the model loads. If the list is empty, see
[Troubleshooting](README.md#the-model-list-is-empty). If the answer is "does not support tools", see
[this entry](README.md#the-answer-is-does-not-support-tools).

---

## Part 6 - Open it to your group

[Part 6](README.md#part-6---open-it-to-your-group) is in the guide. Here are its commands for macOS.

### Open it to the local network

This is step 1 of [before the first session](README.md#before-the-first-session). Your
administrator account must exist ([part 3](#step-6---create-your-administrator-account)), and Open
WebUI must be running (if you stopped it, start it first: see [Commands](#commands)). In the file
of the launch agent, replace `127.0.0.1` (this computer only) with `0.0.0.0` (every network of the
computer), then start Open WebUI again. Its data and accounts are kept, and the restart signs
nobody out:

<!-- ci macos stage=network expect="<string>0.0.0.0</string>" expect="Open WebUI is ready" check="lsof -nP -iTCP:3000 -sTCP:LISTEN" expect="*:3000" -->
```bash
sed -i '' 's|<string>127.0.0.1</string>|<string>0.0.0.0</string>|' ~/Library/LaunchAgents/org.youthailab.owui-local.plist
launchctl bootout gui/$(id -u)/org.youthailab.owui-local
while launchctl print gui/$(id -u)/org.youthailab.owui-local >/dev/null 2>&1; do sleep 1; done
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/org.youthailab.owui-local.plist
grep -o '<string>[0-9.]*</string>' ~/Library/LaunchAgents/org.youthailab.owui-local.plist
until curl -sf http://localhost:3000/health >/dev/null; do sleep 5; done; echo "Open WebUI is ready"
```

The first line changes the file (on a Mac, `sed -i` needs the two quotes `''` after it). The
second one stops Open WebUI, the third one waits until it has stopped, and the fourth one starts it
again. The fifth one must show `<string>0.0.0.0</string>`. The last one waits until you see
`Open WebUI is ready`.

**What you should see.** `<string>0.0.0.0</string>`, then `Open WebUI is ready`. Then type
`lsof -nP -iTCP:3000 -sTCP:LISTEN`: its line now ends with `*:3000 (LISTEN)`, every network of the
computer. Then go back to [the guide](README.md#before-the-first-session), at the end of step 1:
open <http://localhost:3000>.

**The firewall of the Mac.** If it is on (**System Settings** → **Network** → **Firewall**), macOS
asks, in a window, whether to allow the program to accept incoming network connections: when Open
WebUI starts again open to the network, or the first time a phone tries to open it. Look at the
screen of the Mac after this block. Until you answer, the connections are refused. Click
**Allow** ([Apple](https://support.apple.com/guide/mac-help/block-connections-to-your-mac-with-a-firewall-mh34041/mac)).
The program may be named `python3.12` in this window, not Open WebUI. (not tested)

If you clicked **Deny**, or the phones still cannot open the address: **System Settings** →
**Network** → **Firewall** → **Options**, find the program in the list, and choose to allow its
incoming connections. (not tested)

### Find the address of the computer

```bash
ipconfig getifaddr "$(networksetup -listallhardwareports | awk '/Hardware Port: Wi-Fi/{getline; print $2}')"
```

**What you should see.** A number, for example `192.168.1.20`: the address of the computer on the
local network. The participants open `http://` followed by this number and `:3000`, for example
`http://192.168.1.20:3000`. The address can change after a restart of the computer.

This command finds the Wi-Fi of the Mac (`en0` on most Macs, `en1` on some Macs with a network
cable socket), then shows its address. If it shows nothing, the Mac is not on a Wi-Fi: see
**System Settings** → **Wi-Fi**. (not tested)

### Keep the Mac awake during a session

A Mac that goes to sleep stops answering the participants. At the start of a session, type in a
terminal:

```bash
caffeinate -i
```

Leave this window open: as long as `caffeinate` runs, the Mac does not go to sleep when nobody uses
it. At the end of the session, press `Ctrl+C` in this window. Keep a laptop plugged in, and its lid
open: we did not test what happens when it is closed.

---

## Delete Open WebUI and its data

At the end of the project, first keep what you want, your instruction files and your documents
([the participants' data](README.md#the-participants-data)). Then type, in the account where Open
WebUI was installed ([part 3](#part-3---start-open-webui)):

<!-- ci macos stage=delete expect="/owui-local/data" check="test ! -e ~/owui-local && test ! -e ~/Library/LaunchAgents/org.youthailab.owui-local.plist && echo removed" expect="removed" -->
```bash
ls -d ~/owui-local/data
launchctl bootout gui/$(id -u)/org.youthailab.owui-local
launchctl enable gui/$(id -u)/org.youthailab.owui-local
rm ~/Library/LaunchAgents/org.youthailab.owui-local.plist
rm -rf ~/owui-local
uv cache clean
```

The first line must show the folder, for example `/Users/anna/owui-local/data`. If it says "No
such file or directory", you are in another account: stop, and change account. The second line
stops Open WebUI: if it shows an error, Open WebUI was already stopped, and you can go on. The third
line removes the stop of [Commands](#commands): macOS keeps it even after the file is deleted, and a
new installation would not start. The next lines delete Open WebUI, and every account,
conversation, memory, feedback, chatbot and document it holds. `uv cache clean` deletes the copies
of the downloads that uv kept (TO BE COMPLETED: how much space this frees on a Mac); it also deletes
what other projects of your account put in this cache. Backups of this computer, for example Time
Machine, may still hold copies. The models of Ollama hold no data of the participants. uv and its
copy of Python stay: they hold no data either. To remove uv and its copy of Python 3.12 too, type
`uv python uninstall 3.12`, then `brew uninstall uv`. If another project of your account uses uv's
Python 3.12, it loses it too.

### Delete Ollama too

This is not needed to delete the data of the participants. To remove Ollama and its models from
the Mac, quit Ollama (icon → **Quit Ollama**), then type:

<!-- ci macos stage=delete check="test ! -e /Applications/Ollama.app && test ! -e ~/.ollama && echo ollama removed" expect="ollama removed" -->
```bash
brew uninstall --cask ollama-app
sudo rm /usr/local/bin/ollama
rm -rf "$HOME/Library/Application Support/Ollama"
rm -rf "$HOME/Library/Saved Application State/com.electron.ollama.savedState"
rm -rf ~/Library/Caches/com.electron.ollama/
rm -rf ~/Library/Caches/ollama
rm -rf ~/Library/WebKit/com.electron.ollama
rm -f ~/Library/Preferences/com.electron.ollama.plist
rm -rf ~/.ollama
```

The first line removes the app; the others are the files of Ollama's own list
([Ollama](https://docs.ollama.com/macos)), plus its settings file from Homebrew's list
([Homebrew](https://formulae.brew.sh/cask/ollama-app)). That list writes two of these folders as
`"~/Library/..."`: between quotes, the terminal does not replace `~` with your home folder, and
the line deletes nothing. Here they start with `$HOME`, which works between quotes.

If the first line says that `ollama-app` is not installed, Ollama was on this Mac before this
guide: quit it, drag **Ollama** from **Applications** to the Trash, then type the other lines.

---

## Commands

| Command | What it does |
|---|---|
| `launchctl disable gui/$(id -u)/org.youthailab.owui-local && launchctl bootout gui/$(id -u)/org.youthailab.owui-local` | stops Open WebUI, also after a restart of the Mac (its data is kept) |
| `launchctl enable gui/$(id -u)/org.youthailab.owui-local && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/org.youthailab.owui-local.plist` | starts Open WebUI again, also after the next restarts; wait a minute before you open it |
| `launchctl print gui/$(id -u)/org.youthailab.owui-local \| grep "state ="` | shows whether Open WebUI is running (`state = running`) |
| `tail -n 20 ~/owui-local/open-webui.log` | shows the last messages of Open WebUI |
| `cd ~/owui-local && source venv/bin/activate` | activates the virtual environment of Open WebUI, to use `python` or `uv pip` in it |
| `ipconfig getifaddr "$(networksetup -listallhardwareports \| awk '/Hardware Port: Wi-Fi/{getline; print $2}')"` | shows the address of the computer on the Wi-Fi |
| `caffeinate -i` | keeps the Mac awake until you press `Ctrl+C` |
| `brew upgrade uv` | updates uv to its latest version |

The commands of Ollama (`ollama pull`, `ollama list`, `ollama ps`) are the same on every system:
see [Commands](README.md#commands) in the guide.

---

## Troubleshooting

### "command not found: brew"

Type `eval "$(/opt/homebrew/bin/brew shellenv zsh)"`, then `brew --version`. If it works, add the
three lines of [part 1, step 3](#step-3---check-for-homebrew-or-install-it), so that the next
terminals find `brew` too. If it still says "no such file or directory", Homebrew is not installed:
see the same step.

### "Ollama is ready" never appears

Press `Ctrl+C`. Look at the screen: a window of macOS or of Ollama may be waiting for an answer
(open an app downloaded from the internet, a password). Answer it, then type the command
`until ollama list ...` of [part 2, step 2](#step-2---keep-ollama-on-this-computer) again. If no
window is there, open Ollama from **Applications**, or read its last messages:
`tail -n 20 ~/.ollama/logs/server.log`.

### "command not found: uv", or "No such file or directory" with `venv/bin/activate`

For uv: type `brew install uv` ([part 3, step 1](#step-1---install-uv)). For `venv`: type
`cd ~/owui-local` first, or create the virtual environment
([part 3, step 2](#step-2---create-a-virtual-environment)).

### Open WebUI is never ready

Press `Ctrl+C`, then type `tail -n 20 ~/owui-local/open-webui.log`: its last lines say what went
wrong. Show them to someone who can read them if you need help. If the file does not exist, type
`launchctl print gui/$(id -u)/org.youthailab.owui-local | grep "last exit"`: a number other than 0
means that the program could not start. Check also that every step of
[part 3](#part-3---start-open-webui) was done in the same account, in the folder `~/owui-local`:
the launch agent uses the paths of this account.

### `launchctl bootstrap` shows an error

For example `Bootstrap failed: 5: Input/output error`. Open WebUI is probably already started, or
was stopped with the command of [Commands](#commands). Type the command that stops it, then the
command that starts it, from [Commands](#commands). (not tested)

For the other problems, see [Troubleshooting](README.md#troubleshooting) in the guide.
