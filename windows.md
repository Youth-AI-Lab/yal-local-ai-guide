# Windows: install the chatbot on your computer

This page is part of the guide [A chatbot that runs on your own computer](README.md). It holds what
depends on the system of the computer, here **Windows**: parts 1 to 3, the commands of part 6, the
deletion at the end of the project, and the commands and troubleshooting of Windows. It is written
for **Windows 11** on a usual PC (an Intel or AMD processor; a PC with an ARM processor, such as
Snapdragon, is not covered). **We did not follow this page on a
real Windows 11 computer** (not tested). Its commands come from the documentation of each program,
and a machine of GitHub, under Windows Server 2025, ran them from start to end on 29 October 2026
([how](ci/README.md)).

Do parts 1 to 3 on this page. Then go back to the guide for
[part 4](README.md#part-4---build-the-chatbot), [part 5](README.md#part-5---test-it) and
[part 6](README.md#part-6---open-it-to-your-group). When part 6 needs a command, it sends you back
to this page. The words *driver*, *service* and *port* are explained in the
[prerequisites](README.md#prerequisites) of the guide.

Another system: [Linux](linux.md), [macOS](macos.md), [Raspberry Pi](raspberry-pi.md).

> [!WARNING]
> **A technical part.** Parts 1 to 3 use commands typed in PowerShell, some with the administrator
> rights of the computer, and they change its settings. Do them only if you feel confident with
> this.

**The terminal of Windows is PowerShell.** Click **Start**, type `PowerShell`, and open **Windows
PowerShell**. Use this one, which comes with Windows: every command of this page is written for it.
To paste a command, copy it from this page and press `Ctrl+V` in PowerShell, then `Enter`. When you
paste several lines, Windows may first ask whether to paste text with several lines: click **Paste
anyway** (not tested). A few
commands need the **administrator rights**: the page says so. For these, click **Start**, type
`PowerShell`, right-click **Windows PowerShell** and choose **Run as administrator**, then accept
the question of Windows. Its window title starts with "Administrator". Use it only for these
commands.

---

## Part 1 - Check the computer

The speed of a local chatbot depends first on whether the model runs on a **graphics
card**. On the processor alone, our laptop took one to two minutes per answer.
Do this part before part 2.

### Step 1 - Look for a graphics card

In PowerShell, type:

```powershell
Get-CimInstance Win32_VideoController | Select-Object Name
```

**What you should see.** One line per graphics chip, for example an **Intel** or **AMD** chip,
which is part of the processor, and an **NVIDIA** card (not tested).

- **An NVIDIA card**: go to step 2.
- **Only an Intel or AMD chip in the processor**: Ollama will most likely run on the processor (one
  to two minutes per answer on our laptop). Ollama's documentation describes support for some AMD
  Radeon cards on Windows. We did not test it.

### Step 2 - Check that the card works

```powershell
nvidia-smi
```

**What you should see.** A table with the name of the card, its memory, and the version of its
driver (**Driver Version**). We measured with a **6 GB** card (on Linux), and the models of this
guide already overflow it a little ([part 2](#step-4---download-the-model)). We did not test a
smaller card: Ollama would then run a bigger part of the model on the processor, and the answers
would be slower.

Ollama needs an NVIDIA driver of version **551.61 or newer** on Windows
([Ollama](https://docs.ollama.com/windows)). An older card (compute capability 5.0 to 6.2, see the
list of [Ollama](https://docs.ollama.com/gpu)) needs **570 or newer**. A card that is not in this
list runs the model on the processor. We found no official page that says where Windows puts
`nvidia-smi`, or that PowerShell always finds it (not tested). If PowerShell answers that the term
`nvidia-smi` is not recognized, or if the version is older than the one your card needs:

1. Install the driver through **Windows Update** (Microsoft's advice): **Settings** → **Windows
   Update** → **Advanced options** → **Optional updates** → **Driver updates** (not tested). If no
   NVIDIA driver is offered there, use the website of NVIDIA, and nowhere else.
2. Restart the computer.
3. Type `nvidia-smi` again: the card, its memory and the driver version appear.

> [!WARNING]
> Changing the graphics driver can stop the display of a computer. It is the most delicate step of
> this guide: do it only if you feel confident, at a time when the computer is not needed.

---

## Part 2 - Install Ollama and a model

*A technical part, after part 1.* Finish part 1 first.

### Step 1 - Install Ollama

Install it with **winget**, the tool of Windows that installs programs:

<!-- ci windows stage=install check="ollama --version" expect="version" -->
```powershell
winget install --id Ollama.Ollama -e --source winget --accept-source-agreements --accept-package-agreements
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
```

The first command installs Ollama for your account, without the administrator rights. The winget
package of Ollama is not made by Ollama: volunteers of winget maintain it. It downloads the official
installer of Ollama (`OllamaSetup.exe`, from Ollama's page on GitHub) and checks that the file is
the expected one. The last two options say that you accept the terms of winget's list of programs
and of the package; without them, winget asks you.

The installer adds Ollama to the list of folders where Windows looks for programs (the `PATH`), but
only for the windows opened after it. The second line gives this window the new list. You can also
close PowerShell and open a new one.

Ollama then runs in the background, with an icon in the taskbar, near the clock. It starts again
each time you sign in to Windows; to stop this, see the [Ollama FAQ](https://docs.ollama.com/faq)
(Task Manager → **Startup apps**). It also downloads its updates by itself.

**What you should see.** Type `ollama --version`: it answers with a version number. We tested
0.40.8 on Linux; the machine of GitHub got 0.40.13 on Windows Server 2025 (29 October 2026). Ollama
updates itself, so you may see a newer number.

### Step 2 - Keep Ollama on this computer

Ollama also offers **cloud models**, which run on Ollama's servers, not on your computer. Turn this
off, so that no question can leave by mistake
([Ollama](https://docs.ollama.com/faq#how-do-i-disable-ollama-cloud-features)):

<!-- ci windows stage=install -->
```powershell
[Environment]::SetEnvironmentVariable("OLLAMA_NO_CLOUD", "1", "User")
$env:OLLAMA_NO_CLOUD = "1"
```

The first line writes the setting `OLLAMA_NO_CLOUD=1` in the settings of your account: Ollama reads
it each time it starts. The second one gives it to this window too.

Then start Ollama again, so that it reads the setting. This is the procedure of Ollama
([Ollama](https://docs.ollama.com/faq#setting-environment-variables-on-windows)): click the Ollama
icon in the taskbar and quit Ollama, then start **Ollama** again from the **Start** menu. Or type
these lines, which do the same:

<!-- ci windows stage=install -->
```powershell
Stop-Process -Name "ollama app", "ollama", "llama-server" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 5
Start-Process "$env:LOCALAPPDATA\Programs\Ollama\ollama app.exe"
```

The first line stops the programs of Ollama, as its uninstaller does. The last one starts Ollama
again; started from this window, it receives the setting of the second line above.

**What you should see.** Wait until Ollama answers, then check the setting and what Ollama says
about it:

<!-- ci windows stage=install expect="Ollama cloud disabled: true" -->
```powershell
do { Start-Sleep -Seconds 2 } until ($(try { Invoke-WebRequest -UseBasicParsing -ErrorAction Stop http://127.0.0.1:11434/api/version } catch { $null }))
[Environment]::GetEnvironmentVariable("OLLAMA_NO_CLOUD", "User")
Select-String -Path "$env:LOCALAPPDATA\Ollama\server.log" -Pattern "cloud disabled"
```

The first line waits until Ollama answers (a few seconds; if nothing happens after 2 minutes,
press `Ctrl+C`). The second one shows `1`. The third one shows a line with
`Ollama cloud disabled: true`, from the log of Ollama. If not, start Ollama again as above, then
type these three lines again.

The Ollama app also has a setting for its cloud features. With `OLLAMA_NO_CLOUD=1`, it cannot turn
them back on.

Also keep Ollama **for this computer only**, as it is installed: Ollama has no accounts. If it were
opened to the network (for example with `OLLAMA_HOST=0.0.0.0`, an example of its documentation, or
with the setting of its app that exposes it to the network), anyone on your Wi-Fi could use the
model directly, without the rules of your chatbot. Only Open WebUI is for the participants. To
check it, type:

<!-- ci windows stage=install expect="127.0.0.1" -->
```powershell
Get-NetTCPConnection -LocalPort 11434 -State Listen
```

**What you should see.** The column **LocalAddress** shows `127.0.0.1`. If it shows `0.0.0.0` or
`::`, turn off the setting of the Ollama app that exposes it to the network, and remove `OLLAMA_HOST`
from the settings of your account with this command. Then quit Ollama and start it again (not
tested).

```powershell
[Environment]::SetEnvironmentVariable("OLLAMA_HOST", $null, "User")
```

### Step 3 - Choose a model and read its licence

A model is a large file that you download once. Its **licence** says what you may do with it: read
it before you use a model with a group. Use only models without `cloud` in their name.

| Model | Download | Licence | What we saw |
|---|---|---|---|
| `qwen2.5:7b` | 4.7 GB | Apache 2.0 (all sizes of Qwen2.5 except 3B and 72B, [Ollama](https://ollama.com/library/qwen2.5)) | 13 to 15 / 22 with documents |
| `mistral:7b` | 4.4 GB | Apache 2.0 ([Ollama](https://ollama.com/library/mistral)) | 13 to 15 / 22 with documents |
| `phi3.5` | - | MIT ([model card](https://huggingface.co/microsoft/Phi-3.5-mini-instruct)) | broken words: not for young people |

The Apache 2.0 and MIT licences allow the use by an association, and they have no rule on minors.
Other families of models have their own licences and use policies: read them first. For example,
the [Llama 3.1 policy](https://www.llama.com/llama3_1/use-policy/) has rules about minors, and the
[Gemma terms](https://ai.google.dev/gemma/terms) let Google restrict, even remotely, any use it
reasonably believes breaks those terms. We did not measure these models.

### Step 4 - Download the model

<!-- ci windows stage=install -->
```powershell
ollama pull qwen2.5:7b
```

Then check that it runs, and where:

<!-- ci windows stage=install expect="PROCESSOR" -->
```powershell
ollama run qwen2.5:7b "Hello"
ollama ps
```

**What you should see.** An answer, then a line for the model with a column **PROCESSOR**:

- **`100% GPU`**: the model is on the graphics card;
- **`100% CPU`**: the model is on the processor, which is slow. Go back to
  [part 1](#part-1---check-the-computer);
- a split such as `13%/87% CPU/GPU`: the model does not fit entirely on the card. This is what we
  saw on our 6 GB card (on Linux) once the chatbot was set up
  ([part 4](README.md#part-4---build-the-chatbot)), and it was still fast.

---

## Part 3 - Start Open WebUI

*A technical part.* Open WebUI is a Python program. You install it in a folder of its own,
`owui-local`, in your user folder (for example `C:\Users\Anna\owui-local`), and Windows starts it
each time you sign in, on the same computer as Ollama. In this part, only this computer can open
it. You open it to your local network in [part 6](README.md#part-6---open-it-to-your-group), when
your administrator account exists.

Do this whole part in the account of the computer that you will use for Open WebUI, in a normal
PowerShell window (not "Administrator"). Open WebUI will run with the rights of this account.

### Step 1 - Install uv

**uv** is a free tool that installs Python programs, and the version of Python they need. Open
WebUI 0.12.4 needs Python 3.11 or 3.12. uv downloads Python 3.12 for Open WebUI, without changing
any other Python of the computer. uv documents its installation with winget
([uv](https://docs.astral.sh/uv/getting-started/installation/)):

<!-- ci windows stage=install check="uv --version" expect="uv 0.13.6" -->
```powershell
winget install --id astral-sh.uv -e --version 0.13.6 --source winget --accept-source-agreements --accept-package-agreements
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
```

The first command installs uv 0.13.6 for your account. winget may first install a package of
Microsoft that uv needs (Visual C++ Redistributable): if Windows asks whether this program may make
changes, accept. The second line gives this window the new `PATH`, as in
[part 2](#step-1---install-ollama).

**What you should see.** Type `uv --version`: it answers a line that starts with `uv 0.13.6`.

### Step 2 - Create a virtual environment

A **virtual environment** (often called a *venv*) is a folder that holds the programs installed for
one project, apart from the rest of the computer. It uses the Python that uv downloaded. Deleting
the folder deletes these programs. Create the folder of Open WebUI, and its virtual environment
inside, named `venv`:

<!-- ci windows stage=install check=".\venv\Scripts\python.exe --version" expect="Python 3.12" -->
```powershell
New-Item -ItemType Directory -Force -Path "$HOME\owui-local" | Out-Null
Set-Location "$HOME\owui-local"
uv venv --managed-python --python 3.12 venv
```

The first line creates the folder, the second one goes into it. The third one downloads Python 3.12
(about 40 MB) the first time; `--managed-python` makes uv use its own copy, the one we tested, even
if the computer already has a Python 3.12.

On Linux and macOS, the guide **activates** the virtual environment. Not on Windows: activating it
runs a script, and a new Windows PC blocks every script in PowerShell. This page uses the programs of
`venv` directly instead, for example `.\venv\Scripts\python.exe`. You change no security setting of
Windows.

The folder will hold the conversations of your group. Like every folder of the computer, the
administrators of the computer can open it. We did not check whether other accounts of the computer
can (TO BE COMPLETED). To see who can open it, type `icacls "$HOME\owui-local"`: it lists the
accounts and groups that have access (not tested).

**What you should see.** Type `.\venv\Scripts\python.exe --version`: it answers `Python 3.12`
followed by a number. If you close PowerShell before the end of this part, open a new one and type
`Set-Location "$HOME\owui-local"` before you go on.

### Step 3 - Install Open WebUI

<!-- ci windows stage=install check="uv pip show --python venv open-webui" expect="Version: 0.12.4" -->
```powershell
uv pip install --python venv --torch-backend cpu "torch<=2.9.1" open-webui==0.12.4
```

This installs Open WebUI 0.12.4 in `venv` (`--python venv`), with the programs it needs. On our
Linux laptop, it was about 830 MB to download, 2.4 GB once on the disk, and it took 40 seconds.
TO BE COMPLETED: these figures on Windows. We measured the answers with an earlier version, 0.11.4,
on Linux ([About](README.md#about)). Open WebUI uses **torch** to search in
your documents. `--torch-backend cpu` installs the version of torch for the processor: the graphics
card is for Ollama, and the version for the card is a much bigger download. `torch<=2.9.1` is the
version in Open WebUI's own installation, the one we measured.

Then download the small model that Open WebUI uses to search in your documents (about 90 MB). With
the settings of this guide, Open WebUI never downloads anything by itself, so it needs it now:

<!-- ci windows stage=install check="Test-Path (Join-Path $HOME 'owui-local\data\cache\embedding\models\models--sentence-transformers--all-MiniLM-L6-v2')" expect="True" -->
```powershell
$env:SENTENCE_TRANSFORMERS_HOME = "$HOME\owui-local\data\cache\embedding\models"
.\venv\Scripts\python.exe -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

The first line says where to keep this model: in the folder of Open WebUI's data. The second one
downloads it.

**What you should see.** Type `uv pip show --python venv open-webui`: it shows `Version: 0.12.4`. The
command that downloads the model may show warnings, for example about "unauthenticated requests",
and a "LOAD REPORT" with the word `UNEXPECTED`: they are normal. It must not end with `Error`. Then type
`Test-Path "$HOME\owui-local\data\cache\embedding\models\models--sentence-transformers--all-MiniLM-L6-v2"`:
it answers `True`. If it answers `False`, type the two lines again, together, in this window.

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
  address of each phone. An error can still quote what was sent: a request typed by hand, which Open
  WebUI refuses, puts part of its text in the log (we saw it with Open WebUI 0.12.4 on a Linux PC).
  The chat page does not send such requests.

Each line of the file is explained. On Windows, a second file of this guide starts Open WebUI with
these settings: [`owui-start.py`](owui-start.py), a small Python program. It reads `openwebui.env`,
starts Open WebUI, and writes what Open WebUI says in the file `open-webui.log` (its log). Download
both into the folder of Open WebUI:

<!-- ci windows stage=install -->
```powershell
Set-Location "$HOME\owui-local"
curl.exe -fsSLO https://raw.githubusercontent.com/Youth-AI-Lab/yal-local-ai-guide/main/openwebui.env
curl.exe -fsSLO https://raw.githubusercontent.com/Youth-AI-Lab/yal-local-ai-guide/main/owui-start.py
```

Type `curl.exe`, not `curl`: in Windows PowerShell, `curl` is another command. These two files come
from the latest version of this guide. Keep the copies in `owui-local`: Open WebUI always starts
with them, not with the ones on GitHub.

Open WebUI saves most of these settings in its own data at its very first start. After that,
changing the file has no effect on them: you change them in the **Admin Panel**. For example, to
show the banner in the language of your group, change its text after
[step 6](#step-6---create-your-administrator-account), in **Admin Panel** → **Settings** →
**General**, in the part about banners ("Create announcements shown to users in the app."), then
click **Save**.

### Step 5 - Start Open WebUI as a service

On Windows, the **Task Scheduler** starts programs by itself. Copy this whole block into
PowerShell. It creates a task named `owui-local`, which starts Open WebUI each time you sign in to
Windows, then starts it now:

<!-- ci windows stage=install -->
```powershell
$action = New-ScheduledTaskAction -Execute "$HOME\owui-local\venv\Scripts\pythonw.exe" -Argument "owui-start.py 127.0.0.1" -WorkingDirectory "$HOME\owui-local"
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName owui-local -Action $action -Trigger $trigger -Settings $settings -Force
Start-ScheduledTask -TaskName owui-local
```

You can type this block again, for example after an error: it replaces the task.

This task:

- starts Open WebUI on **port 3000** of this computer, for this computer only (`127.0.0.1`), with
  the settings of `openwebui.env`. `pythonw.exe` is the Python of `venv` that opens no window;
- keeps its data (accounts, chatbots, conversations, documents) in the folder
  `owui-local\data`;
- starts it again when you sign in to Windows, not when the computer starts: during a session, this
  account must be signed in. You can lock the screen;
- has no time limit (by default, Windows stops a task after 72 hours), runs on battery, and starts
  Open WebUI again up to 3 times if it stops by accident (not tested).

We did not test an account of an organisation's network (a domain or Microsoft Entra ID), or a user
folder whose name has a space, such as `C:\Users\Anna Smith` (not tested).

Then wait until it is ready:

<!-- ci windows stage=install expect="Open WebUI is ready" check="Get-NetTCPConnection -LocalPort 3000 -State Listen | ForEach-Object { '{0}:{1}' -f $_.LocalAddress, $_.LocalPort }" expect="127.0.0.1:3000" -->
```powershell
do { Start-Sleep -Seconds 5 } until ($(try { Invoke-WebRequest -UseBasicParsing -ErrorAction Stop http://localhost:3000/health } catch { $null }))
"Open WebUI is ready"
```

**What you should see.** `Open WebUI is ready`. TO BE COMPLETED: the time of the first start on
Windows, which prepares the database (22 seconds on our laptop, on Linux).
Then type `Get-NetTCPConnection -LocalPort 3000 -State Listen`: the column **LocalAddress** shows
`127.0.0.1`, so Open WebUI listens for this computer only. If nothing appears after 5 minutes,
press `Ctrl+C` and see [Open WebUI is never ready](#open-webui-is-never-ready).

> [!TIP]
> The file `.webui_secret_key` in `owui-local` keeps the sign-ins valid when Open WebUI starts
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
**Okay, Let's Go!** at the bottom (the participants never see it). Then the chat page of Open WebUI.
Your name at the bottom left opens a menu with **Admin Panel**: you are the administrator. **The
first account becomes the administrator**, and Open WebUI then **closes the sign-ups** by itself.
Nobody else can create an account until you open them in
[part 6](README.md#part-6---open-it-to-your-group).

### Step 7 - Check the connection to Ollama

Click **New Chat**. In the list of models, at the bottom right of the message box, choose
`qwen2.5:7b` (Open WebUI may have chosen another model of Ollama for you). Ask "Hello, who are
you?": the first answer is slower, while the model loads. On our laptop (on Linux), it came after
10 seconds, 5 of them to load the model. If the list is empty, see
[Troubleshooting](README.md#the-model-list-is-empty). If the answer is "does not support tools", see
[this entry](README.md#the-answer-is-does-not-support-tools).

---

## Part 6 - Open it to your group

[Part 6](README.md#part-6---open-it-to-your-group) is in the guide. Here are its commands for
Windows.

### Open it to the local network

This is step 1 of [before the first session](README.md#before-the-first-session). Your
administrator account must exist ([part 3](#step-6---create-your-administrator-account)). It has
three steps: check the network, let port 3000 through the firewall of Windows, then start Open
WebUI again for every network of the computer.

**1. Check the network.** Windows treats each network as **Private** (a network where you know and
trust the people and devices) or **Public** (the default for a new network: the computer is hidden
from the other devices). Type:

<!-- ci windows stage=network -->
```powershell
Get-NetConnectionProfile
```

**What you should see.** The line **NetworkCategory** of your Wi-Fi shows `Private` or `Public`. The
rule of the next step works only on a **Private** network. If it shows `Public`, and only if this is
the Wi-Fi of your organisation, which you trust: open **Settings** → **Network & internet** →
**Wi-Fi** (or **Ethernet**) → your connection, and choose **Private** as its network profile type.
On a Private network, the other devices of the Wi-Fi, the participants' phones included, can find
the computer. Never do this on a Wi-Fi open to anyone, such as the Wi-Fi of a café. On a Private
network, the other programs of the computer that accept connections on Private networks accept them
from this Wi-Fi too. At the end of the project, choose **Public** again.

On a computer managed by your organisation, it can show `DomainAuthenticated`: then the rule below
does nothing. Do not change this network: ask the person who manages the computer to let port 3000
in (not tested).

**2. Let port 3000 in.** In a PowerShell window **as administrator** (see the top of this page),
type:

<!-- ci windows stage=network expect="Open WebUI (group)" -->
```powershell
New-NetFirewallRule -DisplayName "Open WebUI (group)" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow -Profile Private -RemoteAddress LocalSubnet
```

This rule of the Windows firewall lets the devices of your local network (`LocalSubnet`) reach port
3000, on a Private network only.

**What you should see.** The rule, with `Open WebUI (group)` as its name. Close the administrator
window.

> [!IMPORTANT]
> If Windows still shows a window of its firewall about Python, allow the access. **Never click
> Cancel** there: Windows then creates rules that block Python, and they win over the rule above.
> See [the participants cannot connect](#the-participants-cannot-connect). If the account of Open
> WebUI is not an administrator of the computer, Windows blocks Python as soon as Open WebUI opens
> to the network: after step 3, do [the participants cannot connect](#the-participants-cannot-connect)
> at once. (not tested)

**3. Start Open WebUI again, for every network.** In your normal PowerShell window, change the task
so that it gives `0.0.0.0` (every network of the computer) instead of `127.0.0.1` (this computer
only), then start Open WebUI again. Its data and accounts are kept, and the restart signs nobody
out:

<!-- ci windows stage=network expect="owui-start.py 0.0.0.0" -->
```powershell
$action = New-ScheduledTaskAction -Execute "$HOME\owui-local\venv\Scripts\pythonw.exe" -Argument "owui-start.py 0.0.0.0" -WorkingDirectory "$HOME\owui-local"
Set-ScheduledTask -TaskName owui-local -Action $action
Stop-ScheduledTask -TaskName owui-local
Start-Sleep -Seconds 5
Start-ScheduledTask -TaskName owui-local
(Get-ScheduledTask -TaskName owui-local).Actions.Arguments
```

The last command must show `owui-start.py 0.0.0.0`. Then wait until Open WebUI is ready:

<!-- ci windows stage=network expect="Open WebUI is ready" check="Get-NetTCPConnection -LocalPort 3000 -State Listen | ForEach-Object { '{0}:{1}' -f $_.LocalAddress, $_.LocalPort }" expect="0.0.0.0:3000" -->
```powershell
do { Start-Sleep -Seconds 5 } until ($(try { Invoke-WebRequest -UseBasicParsing -ErrorAction Stop http://localhost:3000/health } catch { $null }))
"Open WebUI is ready"
```

**What you should see.** `Open WebUI is ready`, usually within a minute. Then type
`Get-NetTCPConnection -LocalPort 3000 -State Listen`: the column **LocalAddress** shows `0.0.0.0`,
every network of the computer.

Check that Ollama is still for this computer only:

<!-- ci windows stage=network expect="127.0.0.1" -->
```powershell
Get-NetTCPConnection -LocalPort 11434 -State Listen
```

**What you should see.** The column **LocalAddress** shows `127.0.0.1`. If it shows `0.0.0.0` or
`::`, do [the end of step 2](#step-2---keep-ollama-on-this-computer) again. If it answers in red
that it found nothing, Ollama is not running: start **Ollama** from the **Start** menu (not tested).

Then go back to [the guide](README.md#before-the-first-session), at the end of step 1: open
<http://localhost:3000>.

### Find the address of the computer

```powershell
ipconfig
```

**What you should see.** A part for each connection of the computer. In the part of your Wi-Fi (or
Ethernet) connection, the line **IPv4 Address** (in the language of Windows, for example **Adresse
IPv4** in French) shows a number such as `192.168.1.20`: the address
of the computer on the local network. The participants open `http://` followed by this number and
`:3000`, for example `http://192.168.1.20:3000`. The address can change after a restart of the
computer.

### Keep the computer awake during a session

A computer that goes to sleep stops answering the participants. By default, a Windows laptop goes
to sleep after a few minutes without use. Keep it plugged in, and in **Settings** → **System** →
**Power & battery** → **Screen, sleep & hibernate timeouts**, set the sleep time when plugged in to
**Never** (not tested). Or type this command, which changes the same setting (the number is in
minutes; we did not test that `0` means never):

```powershell
powercfg /change standby-timeout-ac 0
```

The account of Open WebUI must also stay signed in ([part 3, step 5](#step-5---start-open-webui-as-a-service)):
you can lock the screen.

---

## Delete Open WebUI and its data

At the end of the project, first keep what you want, your instruction files and your documents
([the participants' data](README.md#the-participants-data)). Then, in the account where Open WebUI
was installed ([part 3](#part-3---start-open-webui)), check that you are in the right account:

<!-- ci windows stage=delete expect="True" -->
```powershell
Test-Path "$HOME\owui-local\data"
```

It must answer `True`. If it answers `False`, you are in another account: stop, and change account.
Then type:

<!-- ci windows stage=delete check="if (-not (Test-Path (Join-Path $HOME 'owui-local')) -and -not (Get-ScheduledTask -TaskName owui-local -ErrorAction SilentlyContinue)) { 'removed' }" expect="removed" -->
```powershell
Set-Location $HOME
Stop-ScheduledTask -TaskName owui-local
Unregister-ScheduledTask -TaskName owui-local -Confirm:$false
Start-Sleep -Seconds 5
Remove-Item -Recurse -Force "$HOME\owui-local"
uv cache clean
```

These lines leave the folder of Open WebUI, stop Open WebUI and delete its task, wait for it to
stop, then delete Open WebUI, and every account, conversation, memory, feedback, chatbot and
document it holds. `uv cache clean` deletes the copies of the downloads that uv kept (TO BE
COMPLETED: the size on Windows); it also deletes what other projects of your account put in this
cache.

**What you should see.** No red error in these lines. Then `Test-Path "$HOME\owui-local"` answers
`False`, and `Get-ScheduledTask -TaskName owui-local` answers, in red, that no task has this name:
this is what you want.

Backups of this computer may still hold copies. The models of Ollama hold no data of the
participants. uv and its copy of Python stay: they hold no data either.

If you opened Open WebUI to the network ([part 6](#open-it-to-the-local-network)), also delete the
rule of the firewall, in a PowerShell window **as administrator**:

<!-- ci windows stage=delete -->
```powershell
Remove-NetFirewallRule -DisplayName "Open WebUI (group)"
```

If you changed your Wi-Fi to **Private** in part 6, choose **Public** again.

**Ollama** is not deleted by these commands. To remove it too: **Settings** → **Apps** → **Installed
apps** → **…** next to Ollama → **Uninstall** (not tested). Its uninstaller also deletes the models,
if you leave its box checked (it is, by default). Then remove the setting of [part
2](#step-2---keep-ollama-on-this-computer):
`[Environment]::SetEnvironmentVariable("OLLAMA_NO_CLOUD", $null, "User")`.

---

## Commands

Type them in PowerShell, in the account where Open WebUI is installed.

| Command | What it does |
|---|---|
| `nvidia-smi` | shows the NVIDIA card, its memory and its driver |
| `Stop-ScheduledTask -TaskName owui-local; Disable-ScheduledTask -TaskName owui-local` | stops Open WebUI, also after you sign in again (its data is kept) |
| `Enable-ScheduledTask -TaskName owui-local; Start-ScheduledTask -TaskName owui-local` | starts Open WebUI again, now and each time you sign in |
| `Get-ScheduledTask -TaskName owui-local` | shows whether Open WebUI is running (**State**: `Running`) |
| `Get-Content -Tail 20 "$HOME\owui-local\open-webui.log"` | shows the last messages of Open WebUI |
| `Set-Location "$HOME\owui-local"` | goes to the folder of Open WebUI, to use `.\venv\Scripts\python.exe` or `uv pip ... --python venv` |
| `ipconfig` | shows the address of the computer on the local network (**IPv4 Address**, in the language of Windows: **Adresse IPv4** in French) |
| `winget upgrade --id astral-sh.uv -e` | updates uv to its latest version |

The commands of Ollama (`ollama pull`, `ollama list`, `ollama ps`) are the same on every system:
see [Commands](README.md#commands) in the guide.

---

## Troubleshooting

### "winget", "uv" or "ollama" is not recognized

**winget**: on a new PC, Windows installs it in the background after the first sign-in
([Microsoft](https://learn.microsoft.com/en-us/windows/package-manager/winget/)). Open the
**Microsoft Store** and update **App Installer**, then open a new PowerShell. Or type the command of
Microsoft that asks Windows to register it now (it does not download it), then open a new
PowerShell (not tested):

```powershell
Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe
```

**uv** or **ollama**: PowerShell does not know the new folders of the `PATH` yet. Close PowerShell
and open a new one, or
type `$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")`.

### "running scripts is disabled on this system"

You tried to activate the virtual environment, or to run another script. This page never needs it:
use the programs of `venv` directly, as in [part 3](#step-2---create-a-virtual-environment), from
the folder `owui-local` (`Set-Location "$HOME\owui-local"`).

### "Access is denied" with Register-ScheduledTask or Set-ScheduledTask

We did not test whether these commands need the administrator rights for a task of your own
account (not tested). If Windows refuses, type the same block in a PowerShell window **as
administrator**, opened from your own account: the task still runs Open WebUI with your account.
This works only if your account is itself an administrator of the computer. If Windows asks for the
password of another account, click **No**: the commands would use the folders of that other
account. Ask the person who manages the computer to make your account an administrator for the
installation. (not tested)

### Open WebUI is never ready

Press `Ctrl+C`, then type `Get-Content -Tail 20 "$HOME\owui-local\open-webui.log"`: its last lines
say what went wrong. Show them to someone who can read them if you need help. If the file does not
exist, the task did not start: check with `Get-ScheduledTask -TaskName owui-local`. Check also that
every step of [part 3](#part-3---start-open-webui) was done in the same account, in the folder
`owui-local`: the task uses the paths of this account. If another program uses port 3000,
`Get-NetTCPConnection -LocalPort 3000 -State Listen` shows it in **OwningProcess** (a number); stop
this program first.

### The participants cannot connect

First check step 1 of [Open it to the local network](#open-it-to-the-local-network): the network must
be **Private**, or the rule does nothing. If someone clicked **Cancel** on a window of the firewall,
or if this account is not an administrator, Windows has created rules that block Python, and they
win over the rule of this page. To see the blocking rules, type in a PowerShell window **as
administrator**:

```powershell
Get-NetFirewallRule -Direction Inbound -Action Block | Format-Table DisplayName, Profile
```

A rule whose name mentions Python blocks Open WebUI. This command, in the same window, deletes only
the blocking rules for the Python of uv or of `owui-local`, not those of other programs (not
tested):

```powershell
Get-NetFirewallRule -Direction Inbound -Action Block | Where-Object { ($_ | Get-NetFirewallApplicationFilter).Program -match '\\uv\\|owui-local' } | Remove-NetFirewallRule
```

Then type the first command again. If a blocking rule for Python is still in the list, show this
list to someone who can read it.

For the other problems, see [Troubleshooting](README.md#troubleshooting) in the guide.
