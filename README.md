# A chatbot that runs on your own computer

## Youth AI Lab — Erasmus+ project

- **Partners:** L.A.B. (Aix-en-Provence), UAB (Barcelona), Perlatecnica (Naples), Digitale Wolven
  (Antwerp), CSC Vent des Îles (La Rochelle)
- **Need help?**
  - Read the [Troubleshooting](#troubleshooting) section at the end of this guide.
  - Look at, or open, an [issue](https://github.com/Youth-AI-Lab/yal-local-ai-guide/issues).

> **Your chatbot, without an AI company.** In the
> [Open WebUI guide](https://github.com/Youth-AI-Lab/yal-openwebui-guide), each question of your
> group goes to an AI company, paid with an API key. Here, the AI model runs on a computer of your
> organisation: **the questions of your group stay on this computer**, and there is no key to buy
> and no cost per question. You install two free programs on this computer: **Ollama**, which runs
> the AI model, and **Open WebUI**, the chatbot tool of the Open WebUI guide. Parts 1 to 3 are
> technical: do them only if you feel confident with a terminal and the administrator rights of a
> computer.

This guide is for youth workers, facilitators and educators who work with young people (12 to 25).
It goes with the [Open WebUI guide](https://github.com/Youth-AI-Lab/yal-openwebui-guide). That
guide shows how to build, test and share a chatbot. This one shows what changes when the model runs
on your own computer, with the numbers we measured.

---

## Goals

### What you will be able to do

| Part | Kind | You will be able to... |
|---|---|---|
| **1. Check the computer** | technical | Say whether a computer is fast enough, and make its graphics card work for the AI. |
| **2. Install Ollama** | technical | Install the program that runs the model, and download a model whose licence you have read. |
| **3. Start Open WebUI** | technical | Start the chatbot tool on the same computer, with your administrator account. |
| **4. Build the chatbot** | in the browser | Make a chatbot from your documents, with the settings a small model needs. |
| **5. Test it** | in the browser | Check its answers and its speed before a session. |
| **6. Open it to your group** | technical the first time | Let the participants use it from their phones, on your local network, during a session. |

At the end, you will also know what we measured, where the participants' data stays, how to
delete it, and what a local model cannot do.

### Why this approach?

**The questions stay in your organisation.** With an API key, as in the Open WebUI guide, each
question is sent to the company that runs the model, often outside the European Union. Here, the
model runs on your computer: the questions, your documents and the answers are processed there.
Some organisations ask for this when the participants are minors.

**No key, no cost per question.** Ollama and the models of this guide are free. What you pay for is
the computer and its electricity.

**A small model needs your documents.** The models that run on a laptop are much smaller than the
models of AI companies. Without documents, they invent: in our test, they scored 4 or 5 out of 22.
With the documents of the workshop, given to them the right way, they scored 13 to 15 out of 22
([what we measured](#what-we-measured)).

**A graphics card makes it usable.** On the processor alone, an answer with documents took one to
two minutes. With the small graphics card of a laptop, it took 6 to 9 seconds.

### Is this guide for you?

**You can use an API key**, and your organisation agrees that the questions go to an AI company:
the [Open WebUI guide](https://github.com/Youth-AI-Lab/yal-openwebui-guide) is simpler. It works
in a browser, with nothing to install.

**Your organisation wants the conversations of the young people to stay in the organisation**, or
cannot pay for a key: this guide is for you. Parts 1 to 3 install programs and change the settings
of the computer, with commands typed in a terminal. If you do not feel confident with this, ask
someone who is to do them with you.

**Your organisation already gives you a chatbot tool**: use it first. It has been checked by your
organisation, and the participants may already know it.

### Prerequisites

- **A computer** that stays on during the session, ideally with an **NVIDIA graphics card with at
  least 6 GB of memory** ([part 1](#part-1---check-the-computer)), and about 20 GB of free disk.
- **Linux**: we tested Ubuntu 26.04. Ollama and Open WebUI also exist for Windows and macOS, but
  the commands of parts 2, 3 and 6 are for Linux, and we did not test the other systems.
- **The administrator rights** of this computer. You do not need Python or anything else
  beforehand: part 3 installs the version of Python that Open WebUI needs, in its own folder.
- **A good internet connection** the first time: Open WebUI and what it needs are a download of
  about 1 GB (about 3 GB once on the disk), a model 4.4 to 4.7 GB, plus Ollama and, if needed, a
  graphics driver.

**Words used in this guide.** A **terminal** is the window where you type commands (on Ubuntu:
`Ctrl+Alt+T`). Commands that start with `sudo` run with the administrator rights: the terminal asks
for the computer's password. A **driver** is the program that lets the computer use a piece of
hardware, here the graphics card. A **service** is a program that the computer starts by itself and
keeps running in the background. A **port** is the number after an address, here 3000: it tells
the computer which program should answer.

**Are you ready?** You are if you have built a chatbot with the
[Open WebUI guide](https://github.com/Youth-AI-Lab/yal-openwebui-guide), or if you know which
documents your chatbot should know, and what it should refuse to do.

---

## What we measured

We asked the **11 test questions** of the [workshop kit](https://github.com/Youth-AI-Lab/yal-workshop-kit)
to local models, on 28 October 2026. The questions are about fire prevention: figures, local rules,
a question with no answer in the documents, an out-of-scope question, two sources that disagree. Each
answer got a score on the scale of the workshop: **2** right and with its source, **1** honest but
not enough, **0** wrong or invented. The scores below are those of an **automatic judge** (an AI
model that compares each answer with the expected one). TO BE COMPLETED: the check of these scores
by a person, which may move a total by one or two points.

The computer was a laptop **Lenovo ThinkPad P14s Gen 6** (Intel Core Ultra 7 255H processor, 30 GB
of memory). We used it first with its **processor only**, then with its **NVIDIA RTX PRO 500
graphics card (6 GB)**. Software: Ollama 0.40.8 and Open WebUI v0.11.4 with its default document
search (the one [`openwebui.env`](openwebui.env) keeps), and the documents of the workshop kit
(summaries and official texts).

| Model | Score without documents | Score with the documents | Time per answer with the documents, processor only | Time per answer with the documents, graphics card |
|---|---|---|---|---|
| `qwen2.5:7b` | 5 / 22 | 13 / 22 (processor), 15 / 22 (card) | 73 s (47 to 130 s) | **6 s** (3 to 12 s) |
| `mistral:7b` | 4 / 22 | 15 / 22 (processor), 13 / 22 (card) | 95 s (62 to 159 s) | **9 s** (4 to 34 s) |
| `phi3.5` | 5 / 22 | not measured | — | — |

The times are the middle answer (the median), then the fastest and the slowest. They include the
search in the documents. With the card, the slowest answer of `mistral:7b` (34 s) was the first
one, while the model was loading. Without documents, on the processor, the middle answer took 35 to
49 seconds.

Between the processor series and the card series, each model gained or lost 2 points: one went up,
the other down. So do not choose between `qwen2.5:7b` and `mistral:7b` from these numbers: both
did about as well.

**What the answers showed:**

- **Without documents, the models invent.** Asked about the "Pla Alfa", the fire danger plan of
  Catalonia, one model described a plan for road traffic, another a programme on digital skills for
  children, the third a hygiene grade for restaurants. One placed the French forest fire forecast,
  "Météo des forêts", in Quebec. None refused the out-of-scope question.
- **With the documents, they answer much better**: the right figures, with their source, and "I
  don't know" when the documents have no answer. Some mistakes came from the search: when the
  answer was only in a long official text, the search did not always find it, and when two
  documents disagreed, the search sometimes brought back only one of them. Other mistakes came from
  the model: it misread a passage it had been given, said "I don't know" when the answer was in its
  passages, or gave a wrong source.
- **The small model we tested did not search by itself.** When Open WebUI let `qwen2.5:7b` decide
  when to search the documents, it never did, and scored 7 out of 22. This is why
  [part 4](#part-4---build-the-chatbot) changes one setting.
- **`phi3.5` wrote broken words** in almost every answer ("2decade", "Inadezymes"). It is not for
  young people.

**Several participants at once.** We sent 1, 2, 4 and 8 questions at the same moment to
`qwen2.5:7b` on the 6 GB card. The model answers them **one after the other**. The last participant
served saw the first words of the answer after **3 s** (1 question), **8 s** (2), **20 s** (4) and
**50 s** (8). With this card, count about **four questions at the same moment** before the wait gets
too long for a group. Young people do not all ask at the same second, but an activity where
everybody starts together reaches this limit.

**What we did not measure:**

- other languages than English: our questions were in English (we tried a single question in
  French, see [part 5](#part-5---test-it)), so test yours in the language of your group (for
  example Catalan, Dutch, French or Italian);
- bigger models, and other families of models (Gemma, Llama);
- a graphics card with less than 6 GB, Windows and macOS;
- the electricity used;
- the Ollama setting that answers several questions in parallel (`OLLAMA_NUM_PARALLEL`).

---

## Part 1 - Check the computer

> [!WARNING]
> **A technical part.** Parts 1 to 3 use commands typed in a terminal, some with the administrator
> rights of the computer (`sudo`), and they change its settings. Do them only if you feel confident
> with this.

The speed of a local chatbot depends first on one thing: whether the model runs on a **graphics
card**. On the processor alone, our laptop took one to two minutes per answer.
Do this part before part 2.

### Step 1 - Look for a graphics card

Open a terminal and type:

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

In both cases:

1. List the drivers Ubuntu offers: `sudo ubuntu-drivers list`
2. Install the driver it lists. For a recent card, choose the version whose name ends with
   **`-open`**: on Ubuntu, these packages use the open modules. On our laptop, it was
   `sudo apt install nvidia-driver-595-open`
3. Restart the computer.
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

On Linux, the official installation is one line ([Ollama](https://docs.ollama.com/linux)):

<!-- ci linux stage=install check="ollama --version" expect="version" -->
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

It installs Ollama as a service that starts with the computer. On Windows and macOS, use the
installers of <https://ollama.com/download> (not tested for this guide).

**What you should see.** `ollama --version` answers with a version number. We tested 0.40.8.

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
  saw on our 6 GB card once the chatbot was set up ([part 4](#part-4---build-the-chatbot)), and it
  was still fast.

---

## Part 3 - Start Open WebUI

*A technical part.* Open WebUI is a Python program. You install it in a folder of its own,
`~/owui-local`, and the computer runs it as a service, on the same computer as Ollama. In this
part, only this computer can open it. You open it to your local network in
[part 6](#part-6---open-it-to-your-group), when your administrator account exists.

### Step 1 - Install uv

**uv** is a free tool that installs Python programs, and the version of Python they need. Open
WebUI 0.11.4 needs Python 3.11 or 3.12. Ubuntu 26.04 comes with Python 3.14, which is too new: uv
downloads Python 3.12 for Open WebUI, without changing the Python of the computer.

Do this whole part in a normal account of the computer, the one you will use for Open WebUI, not
as `root`: `whoami` must not answer `root`. Open WebUI will run with the rights of this account.

<!-- ci linux stage=install check="uv --version" expect="uv 0.13.1" -->
```bash
curl -LsSf https://astral.sh/uv/0.13.1/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

The first command installs uv for your user, in `~/.local/bin`. The second one lets this terminal
find it; the next terminals find it by themselves.

**What you should see.** Type `uv --version`: it answers a line that starts with `uv 0.13.1`. If uv
was already installed in `~/.local/bin`, the installer has replaced it with this version.

<details>
<summary><b>On macOS or Windows</b> (not tested)</summary>

<br>

This is for your own computer, with your administrator rights.

**macOS.** Open the app **Terminal** (in **Applications** → **Utilities**), and type the same two
commands as above. The installer puts uv in the folder `.local/bin` of your user folder, as on
Linux.

**Windows.** Open **PowerShell**: in the Start menu, type `PowerShell` and click it. Then type:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.13.1/install.ps1 | iex"
```

Windows does not run a script downloaded from the internet by default: `-ExecutionPolicy ByPass`
allows it for this command only. The installer puts uv in the folder `.local\bin` of your user
folder, and adds this folder to the list where Windows looks for programs (the *PATH*). Close
PowerShell, and open a new one: only the new one finds uv.

**What you should see**, on both: `uv --version` answers a line that starts with `uv 0.13.1`.

The rest of this part is written for Linux. On macOS and Windows, the commands of the next steps
and the service of step 5 are different, and we did not test them.

</details>

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

<!-- ci linux stage=install check="uv pip show open-webui" expect="Version: 0.11.4" -->
```bash
uv pip install --torch-backend cpu "torch<=2.9.1" open-webui==0.11.4
```

This installs Open WebUI 0.11.4, the version we measured, in `venv`, with the programs it needs:
about 1 GB to download, 2.5 GB once on the disk. On our laptop, it took a little more than a minute. Open WebUI uses **torch** to search in your
documents. `--torch-backend cpu` installs the version of torch for the processor: the graphics card
is for Ollama, and the version for the card is a much bigger download. `torch<=2.9.1` is the
version in Open WebUI's own installation, the one we measured.

Then download the small model that Open WebUI uses to search in your documents (about 90 MB). With
the settings of this guide, Open WebUI never downloads anything by itself, so it needs it now:

<!-- ci linux stage=install -->
```bash
SENTENCE_TRANSFORMERS_HOME=$HOME/owui-local/data/cache/embedding/models python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

**What you should see.** `uv pip show open-webui` shows `Version: 0.11.4`. The second command may
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

Then start it, and wait until it is ready:

<!-- ci linux stage=install expect="Open WebUI is ready" check="ss -ltn" expect="127.0.0.1:3000" -->
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now owui-local
until curl -sf http://localhost:3000/health >/dev/null; do sleep 5; done; echo "Open WebUI is ready"
```

**What you should see.** `Open WebUI is ready`, usually within a minute (20 seconds on our laptop).
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
them in [part 6](#part-6---open-it-to-your-group).

### Step 7 - Check the connection to Ollama

Click **New Chat**. In the list of models, at the bottom right of the message box, choose
`qwen2.5:7b` (Open WebUI may have chosen another model of Ollama for you). Ask "Hello, who are
you?": the first answer is slower, while the model loads. On our laptop, it came after 10 seconds,
5 of them to load the model. If the list is empty, see
[Troubleshooting](#the-model-list-is-empty). If the answer is "does not support tools", see
[this entry](#the-answer-is-does-not-support-tools).

---

## Part 4 - Build the chatbot

Follow **[part 2 of the Open WebUI guide](https://github.com/Youth-AI-Lab/yal-openwebui-guide#part-2---build-a-chatbot)**:
gather your documents, write the instructions from a template, create the chatbot. Skip what it
says about the Codespace and VS Code. The templates are in the folder
[templates/ of the Open WebUI guide](https://github.com/Youth-AI-Lab/yal-openwebui-guide/tree/main/templates)
(`topic-assistant.md`, `activity-guide.md`, `project-coach.md`, with filled examples in
`examples/`). Open one, download it with the button **Download raw file**, and fill it in any text
editor on your computer. To paste it into **System Prompt**, select everything under the line
`---`, and copy it.

Everything else is the same, with **three differences** when you create the chatbot:

1. **Base model.** In **Base Model (From)**, choose your Ollama model, for example `qwen2.5:7b`.
2. **Function Calling: Legacy.** In the chatbot's form, under **Model Params**, click **Show** next
   to **Advanced Params**. Find **Function Calling**, and click its button until it reads
   **Legacy**. With this setting, Open WebUI searches your documents before each answer, and gives
   the model the passages it found. With the other settings (**Default**, **Native**), the model
   must decide to search by itself: `qwen2.5:7b` never did, and invented
   ([what we measured](#what-we-measured)). We did not test the other models this way.
3. **num_ctx (Ollama): 8192.** In the same list, find **num_ctx (Ollama)**. Click **Default** so that
   it reads **Custom**: a slider and a number appear. Type **8192** in place of the number. This is the size of the model's memory for one answer
   (its *context window*), in *tokens*, small pieces of words. Ollama's default is 4096 on a
   computer with less than 24 GB of graphics memory. Your instructions, the passages of your
   documents and the answer must all fit in it. We did not test 4096 with documents: we measured
   with 8192, which leaves room.

Then click **Save & Create**.

The Open WebUI guide says that, by default, the chatbot searches its knowledge by itself. That works
with the large models of that guide, but the small local model we tested never searched. Set
**Legacy** on every local chatbot, and check it again on a chatbot you clone or import.

**What you should see.** Ask a question on your topic. In the text of the answer, small grey labels
name the document each part comes from, and the button **Sources** under the answer lists them, as
in step 4 of the Open WebUI guide. The line "Explored list_knowledge…" of that step does not
appear with **Legacy**: Open WebUI searches your documents itself, before the answer. On our laptop,
a question to a chatbot made with the filled example of the template `topic-assistant` and the
summaries of the workshop got its answer in 5 to 6 seconds. Then, in a terminal, type `ollama ps`:
its column **CONTEXT** reads `8192`, the third difference above (**num_ctx**).

**Legacy also keeps each question small.** With the other settings, Open WebUI also describes its
own tools to the model (search, memory, notes…) with each question. On our laptop, a short "Hello,
who are you?" sent that way was about 3,600 tokens: almost all of Ollama's default of 4096, before
any document. A question to our chatbot in **Legacy**, its passages included, was about 2,000
tokens: it leaves room in 8192.

> [!TIP]
> If you already have chatbots from the Open WebUI guide, their instructions and documents work here
> too: create each chatbot again with these three settings.

---

## Part 5 - Test it

Use the method of **[part 3 of the Open WebUI guide](https://github.com/Youth-AI-Lab/yal-openwebui-guide#part-3---test-before-you-open)**:
questions whose answers you know, a question with no answer in your documents, trap questions, a
worried message. Give each answer 2, 1 or 0. Its last paragraph, "test as a participant", uses the
`openwebui share` command: here, do it at the end of [part 6, before each session](#before-each-session) (step 5)
instead. With a local model, check also:

- **The questions with no answer.** A small model invents more easily than a large one. It must say
  "I don't know".
- **The language of your group.** Ask your questions in that language: we only measured English.
  We also asked one question in French, to a chatbot with English documents: the answer was right,
  in French, with its sources. One question is not a measure.
- **The speed.** Time a few answers. Then, once [part 6](#part-6---open-it-to-your-group) is ready,
  ask three or four colleagues to send a question at the same moment from their phones. The last one
  served should see the first words within about twenty seconds.

**A good score is not a green light for young people.** It shows how the chatbot answered your
questions, on that day. The decision to use it with a group belongs to your organisation
([the participants' data](#the-participants-data)).

---

## Part 6 - Open it to your group

The participants use the chatbot from their phones or computers, on the **local network** of your
organisation: the same Wi-Fi as the computer.

> [!IMPORTANT]
> Use the **Admin Panel** only on the computer that runs Open WebUI, at <http://localhost:3000>,
> never from your phone or another computer on the Wi-Fi. The address of the participants starts
> with `http://`, not `https://`: what is typed there, passwords included, crosses the Wi-Fi
> without encryption, and anyone on the same Wi-Fi could read it. Your administrator account opens
> every conversation of the group.

### Before the first session

*A technical part, as parts 1 to 3: commands in a terminal, with the administrator rights.*

1. **Open Open WebUI to the local network.** Your administrator account must exist
   ([part 3](#step-6---create-your-administrator-account)). In the file of the service, replace
   `--host 127.0.0.1` (this computer only) with `--host 0.0.0.0` (every network of the computer),
   then start Open WebUI again. Its data and accounts are kept, and the restart signs nobody out:

   <!-- ci linux stage=network expect="--host 0.0.0.0" check="until curl -sf http://localhost:3000/health >/dev/null; do sleep 5; done; ss -ltn" expect="0.0.0.0:3000" -->
   ```bash
   sudo sed -i 's/--host 127.0.0.1/--host 0.0.0.0/' /etc/systemd/system/owui-local.service
   sudo systemctl daemon-reload && sudo systemctl restart owui-local
   grep -o -- '--host [0-9.]*' /etc/systemd/system/owui-local.service
   ```

   The last command must show `--host 0.0.0.0`. Then wait as in
   [part 3, step 5](#step-5---start-open-webui-as-a-service) until you see `Open WebUI is ready`,
   and open <http://localhost:3000>. If the sign-in page shows, it is only because a sign-in lasts
   12 hours: sign in with your administrator account.
2. **Check that the phones can reach the computer.** Type `hostname -I`: the first number, for
   example `192.168.1.20`, is the address of the computer. On your phone, on the same Wi-Fi as the
   computer (not the mobile network), open `http://` followed by this number and `:3000`, for
   example `http://192.168.1.20:3000`.

   **What you should see.** The sign-in page of Group chatbots. If it does not open, check that the
   address starts with `http://` (some browsers try `https://` first), and that the phone uses the
   same Wi-Fi. Some Wi-Fi networks for guests keep the devices apart: ask the person who manages
   the Wi-Fi of your organisation. If the computer has a firewall turned on, it must let port 3000
   in. The address can change after a restart: if you print a QR code or post the link, ask the
   person who manages the Wi-Fi to give this computer a fixed address.
3. **Make the model under your chatbots safe and reachable.** The participants need to read this
   model for your chatbots to work. But used directly, it has no instructions and no documents: it
   invents, and it refuses nothing ([what we measured](#what-we-measured)). So you give it a safety
   net, then you hide it from their list, and you let them read it. Your name at the bottom left →
   **Admin Panel** → **Settings** → **Models**.
   1. **The safety net.** Click the pencil (**Edit**) on the line of `qwen2.5:7b`, and change three
      things:
      - in **System Prompt**, paste the *Never* rules of your template, then add: "You are not the
        group's chatbot. To any question, answer only: please choose the group's chatbot in the
        list.";
      - click **Show** next to **Advanced Params**, find **Function Calling**, and click its button
        until it reads **Legacy**, as in [part 4](#part-4---build-the-chatbot);
      - under **Capabilities**, uncheck **Builtin Tools**.

      Click **Save & Update**. If "Failed to save model" appears, close the settings window, open
      it again, click the pencil again, and do the three changes again. Do all three: we tested
      them together. On our laptop, with the System Prompt alone, the model still received Open
      WebUI's tools with each question, and ignored the instruction. With the three changes, it
      answered as asked.
   2. **Hide it, then let the participants read it.** On the same line, click **…** (**More**) →
      **Hide Model**, then **…** again → **Make Public**, in this order.
   3. **Check.** Close the settings window, open **Settings** → **Models** again, and click **…** on
      the line of `qwen2.5:7b`: it should now offer **Show Model** and **Make Private**. If not, do
      the missing one again. Then click the pencil: the three changes of the safety net should still
      be there.

   Hidden, the model is no longer in the participants' list: they see only your chatbots, and one
   of them is already chosen when they open a new chat.
   But hiding is not a lock: a participant who knows its name can still reach it, for example by
   typing the address with `?model=qwen2.5:7b`. Then the safety net answers. It applies only when
   someone uses the model directly: your chatbots keep their own instructions.

### Before each session

1. **Check the address**: `hostname -I`.
2. **Start Open WebUI** if you stopped it after the last session:
   `sudo systemctl enable --now owui-local`.
3. **Check the sign-ups and the accounts.** In **Admin Panel** → **Settings** → **Authentication**,
   **New Sign Ups** must be off (if you forgot last time, turn it off and click **Save**). In
   **Admin Panel** → **Users**, check that you know every account.
4. **Give the participants access to your chatbot.** In Open WebUI, a new chatbot is **Private**:
   only you can use it. A participant needs to read the chatbot, its documents and the model under
   it (set up in [before the first session](#before-the-first-session), step 3: safety net,
   hidden, public; do the whole of step 3 again for a model you download later). Otherwise the
   chatbot is missing from their list, answers "Model not found", or answers without its documents.
   - **The chatbot**: **Workspace** → **Models** → **…** at the end of the line of your chatbot →
     **Edit** → **Access** (next to its name) → choose **Public** ("Accessible to all users").
     Close the window, then click **Save & Update**.
   - **Its documents**: **Workspace** → **Knowledge** → open your knowledge → **Access** → choose
     **Public**. Open WebUI saves it at once.
   - **Several groups**: every account sees every **Public** chatbot. In **Workspace** → **Models**,
     switch on only the chatbots of this group, and switch the others off.
5. **Test it as a participant**, from your own phone on the same Wi-Fi. No phone at hand: on the
   computer, open a private window of the browser (`Ctrl+Shift+P` in Firefox, `Ctrl+Shift+N` in
   Chrome), so that you are not signed in as the administrator there, and type the address of
   step 1 followed by `:3000`, for example `http://192.168.1.20:3000`, not `localhost`. Open
   the sign-ups as in [During the session](#during-the-session), create a test account such as
   `test@group.local`, and check that its list of models shows only your chatbots. Ask one
   question, and check that the answer shows the grey labels of your documents. Then open the
   address followed by `/?model=qwen2.5:7b`, and say "Hello" in this new chat: the model should
   answer only that you must choose the group's chatbot. Then close the sign-ups again.

### During the session

1. On the computer itself (<http://localhost:3000>): your name at the bottom left → **Admin Panel**
   → **Settings** → **Authentication**. Turn **New Sign Ups** on. In **Default User Role**, choose
   `user` (never `admin`), or keep `pending` if you prefer to approve each account in the list of
   users. Click **Save**.
2. Give the participants the address of the day: on the board, or as a QR code if `qrencode` is
   installed: `qrencode -t ANSI http://YOUR-ADDRESS:3000`, where `YOUR-ADDRESS` is the number that
   `hostname -I` shows today.
3. **On a shared tablet or computer**, each participant clicks their name at the bottom left →
   **Sign Out** before handing it over. Closing the tab is not enough.
4. The rest is as in
   **[part 5 of the Open WebUI guide](https://github.com/Youth-AI-Lab/yal-openwebui-guide#part-5---open-it-to-your-group)**:
   the participants sign up with a nickname, never their real name, and give feedback with the
   thumbs. Skip its steps about the Codespace, GitHub's warning page and the PORTS tab. Where it
   says `openwebui share open`, `share status` or `share close`, do this instead:
   - **Count the accounts**: in **Admin Panel** → **Users**, on your own screen, never projected.
     While sign-ups are open, anyone on your Wi-Fi who has the address can create an account.
     Delete the accounts you do not know.
   - **A chatbot or documents created or changed during the session**: make them **Public** again
     ([before each session](#before-each-session), step 4). If you do not, the participants do not
     see a new chatbot, and a changed chatbot can answer without its new documents.

### After the session

1. Turn **New Sign Ups** off again, and click **Save**.
2. Should the participants use the chatbot only during sessions? Then stop it:
   `sudo systemctl disable --now owui-local`. It stays stopped, even after a restart of the
   computer, until `sudo systemctl enable --now owui-local`. If it stays on, the participants can use it at any time on the
   Wi-Fi, without you: say so in the notice for the participants.

The accounts stay: the participants can come back next time, at the address of the day.

---

## The participants' data

**Where it stays.** The accounts, the conversations, what the chatbot remembers about each
participant (if its **Memory** is on), your documents and the feedback are stored on this
computer, in the folder `~/owui-local/data`. The questions are answered by the model on this
computer: they are not sent to an AI company. Your administrator account in Open WebUI, anyone
with the administrator rights of the computer, and anyone who uses the computer's account where
Open WebUI is installed can read this data. Use this account only for Open WebUI and for you, lock
the screen when you leave the computer, and choose a strong administrator password. Decide with
your organisation who may read the data, and when it is deleted.

**What still goes out, or can be seen.**
- The downloads: Ollama, the models, uv, Python, Open WebUI and its search model come from the
  internet, the first time.
- With [`openwebui.env`](openwebui.env), Open WebUI is set not to send anything by itself, and
  Ollama's cloud features are off ([part 2](#step-2---keep-ollama-on-this-computer)). We did not
  check the network traffic of either program. If your organisation needs a complete answer, have
  it checked by someone who can.
- On the Wi-Fi, the questions and the passwords travel without encryption (`http://`).
- Files: the upload buttons are hidden, but a participant with technical skills can still store a
  file or a photo on this computer.

**Deleting the data.**
- *A participant asks to delete their data*: follow
  [the Open WebUI guide](https://github.com/Youth-AI-Lab/yal-openwebui-guide#a-participant-asks-to-delete-their-data),
  in the same order. Where it says `openwebui reset`, the last resort here is the full deletion
  below.
- *At the end of the project*: first keep what you want, your instruction files and your
  documents. Then type, in the account where Open WebUI was installed
  ([part 3](#part-3---start-open-webui)):

  <!-- ci linux stage=delete expect="/owui-local/data" check="test ! -e ~/owui-local && ! systemctl cat owui-local >/dev/null 2>&1 && echo removed" expect="removed" -->
  ```bash
  ls -d ~/owui-local/data
  sudo systemctl disable --now owui-local && sudo rm /etc/systemd/system/owui-local.service
  sudo systemctl daemon-reload
  rm -rf ~/owui-local
  uv cache clean
  ```

  The first line must show the folder, for example `/home/anna/owui-local/data`. If it says "No
  such file or directory", you are in another account: stop, and change account. The next lines
  delete Open WebUI, and every account, conversation, memory, feedback, chatbot and document it
  holds. `uv cache clean` deletes the copies of the downloads that uv kept (about 2.7 GB). Backups
  of this computer may still hold copies. The models of Ollama hold no data of the participants.
  uv and its copy of Python stay: they hold no data either.

**Before any use with young people, your organisation decides**: whether a chatbot fits this group,
who informs the participants and their parents, how long the data is kept. A local model changes
who receives the questions. It does not change these questions. The
[OpenCode guide](https://github.com/Youth-AI-Lab/yal-opencode-guide#before-any-use-with-a-group-your-organisation-decides)
lists the rules to check: a data protection impact assessment, the rule on consent, and telling
people they talk with an AI (GDPR, the European AI Act). Its first points, an account with a key and
a contract with the company that runs the model, are for a model paid by the question. With a local
model there is no key and no such company: your organisation's own rules for its computers and its
data apply instead.

**Tell the participants.** The folder [`templates/`](templates/) of this guide has a notice for
the participants: the local version of the notice of the Open WebUI guide. It says that the
questions stay on the organisation's computer. (The instruction templates are in the
[Open WebUI guide](https://github.com/Youth-AI-Lab/yal-openwebui-guide/tree/main/templates).)

**The rules of a chatbot are not a lock.** As with any chatbot, a participant who insists can make
it say something its instructions forbid. Read the feedback after each session.

---

## Costs

**No cost per question.** Ollama, Open WebUI and the models of this guide are free.

**The computer.** A graphics card makes the difference: on our laptop, the NVIDIA RTX PRO 500
(6 GB) made each answer about ten times faster than the processor alone. We did not measure the
electricity.

---

## Limits to know

- **Slow without a graphics card**: one to two minutes per answer on the processor alone.
- **One question at a time**: with our 6 GB card, about four questions at the same moment before
  the wait gets too long.
- **A small model invents without documents**, and the one we tested did not search them by itself:
  keep **Function Calling: Legacy**.
- **The search can miss, and the model can misread.** An answer that is only in a long text may not
  come back. When two documents disagree, the chatbot may give only one side. Write short, clear
  documents, as the Open WebUI guide advises, and test your chatbot ([part 5](#part-5---test-it)).
- **The scores move**: one model gained 2 points between our two series, the other lost 2.
- **Languages**: we measured English only.
- **The computer must stay on, on the same network** as the participants.
- **No encryption on the Wi-Fi** (`http://`).
- **The model under your chatbots is reachable** by a participant who knows its name: give it a
  safety net ([part 6](#before-the-first-session)).

---

## Commands

| Command | What it does |
|---|---|
| `nvidia-smi` | shows the NVIDIA card and its memory |
| `ollama pull qwen2.5:7b` | downloads a model |
| `ollama list` | lists the downloaded models |
| `ollama ps` | shows the loaded model, and whether it runs on the card (`GPU`) or on the processor (`CPU`) |
| `sudo systemctl disable --now owui-local` / `sudo systemctl enable --now owui-local` | stops or starts Open WebUI, also after a restart of the computer (its data is kept) |
| `systemctl status owui-local` | shows whether Open WebUI is running (`active (running)`); `q` to quit |
| `sudo journalctl -u owui-local -n 20 --no-pager` | shows the last messages of Open WebUI |
| `cd ~/owui-local && source venv/bin/activate` | activates the virtual environment of Open WebUI, to use `python` or `uv pip` in it |
| `hostname -I` | shows the address of the computer on the local network |

---

## Troubleshooting

### The answers take more than a minute

Type `ollama ps` while an answer is being written. If **PROCESSOR** reads `100% CPU`, the model
runs on the processor: see [part 1](#part-1---check-the-computer). If `nvidia-smi` does not find the
card, the driver is the cause ([step 2](#step-2---check-that-the-card-works)). The first question
after a pause is always slower: the model loads again. By default, it stays loaded 5 minutes.

### The chatbot answers without its documents

Its answers show no grey labels of your documents and no **Sources** button. Check **Function
Calling: Legacy** and **num_ctx (Ollama): 8192** in its **Advanced Params**
([part 4](#part-4---build-the-chatbot)), and that its knowledge is selected. A bare **[1]** in the
text, with no label, means that the model wrote a citation but received no passages. If this
happens to the participants only, check that its documents are **Public**
([part 6](#before-each-session)).

### The model list is empty

Open WebUI does not reach Ollama. Check that Ollama runs (`ollama list` answers). Then open
**Admin Panel** → **Settings** → **Connections**. Check that **Ollama API** is on. Under **Manage
Ollama API Connections**, click the gear icon (**Configure**) at the end of the address line, not the
arrow (**Manage**). Type `http://127.0.0.1:11434` in **URL**, click the two circling arrows
(**Verify Connection**) to the right of it, then click **Save**. Open WebUI keeps the address it had at its very
first start: starting it again with another `OLLAMA_BASE_URL` does not change it.

Do not open Ollama to the network to fix this ([part 2](#step-2---keep-ollama-on-this-computer)).

### The answer is "does not support tools"

The model you chose cannot use Open WebUI's tools, which Open WebUI offers by default. This happened
with `phi3.5`. In the list of models, at the bottom right of the message box, choose `qwen2.5:7b`,
or one of your chatbots: they are set to **Legacy** ([part 4](#part-4---build-the-chatbot)), which
sends no tools.

### "Model not found"

For you: reload the page of Open WebUI, then ask again. If it persists, check that the base model of
the chatbot is still in `ollama list`.

For a participant: the chatbot, its documents or the model under it is not **Public**
([before each session](#before-each-session), step 4).

### "uv: command not found", or "No such file or directory" with `venv/bin/activate`

For uv: type `export PATH="$HOME/.local/bin:$PATH"`, or open a new terminal. For `venv`: type
`cd ~/owui-local` first, or create the virtual environment
([part 3, step 2](#step-2---create-a-virtual-environment)).

### `uv venv` ends with an error about Python 3.12

uv could not download Python 3.12. Check the internet connection, then type the command again.

### Open WebUI is never ready

Press `Ctrl+C`, then type `sudo journalctl -u owui-local -n 20 --no-pager`: its last lines say what
went wrong. Show them to someone who can read them if you need help. Check also that every step of [part 3](#part-3---start-open-webui) was done by the
same user, in the folder `~/owui-local`: the service uses the paths of this user.

### The address does not open after a restart of the computer

Type `hostname -I`: if the number changed, give the participants the new address. Open WebUI should
start by itself, unless you stopped it after the last session: type
`sudo systemctl enable --now owui-local`, then wait a minute.

### The participants cannot open the address

Try from your own phone, on the same Wi-Fi. If it does not open, check the address (`hostname -I`)
and step 1 of [before the first session](#before-the-first-session). If it still does not open,
the Wi-Fi or a firewall keeps it out: see step 2 of [before the first session](#before-the-first-session).

---

## Going further

These links were checked in October 2026.

- [The Open WebUI guide](https://github.com/Youth-AI-Lab/yal-openwebui-guide): build, test and
  share chatbots, with templates for a topic, an activity or a project.
- [The OpenCode guide](https://github.com/Youth-AI-Lab/yal-opencode-guide): a chatbot in a terminal,
  and the rules to check before any use with young people.
- [The workshop kit](https://github.com/Youth-AI-Lab/yal-workshop-kit): what is behind each part of a
  chatbot, step by step.
- Ollama: [documentation](https://docs.ollama.com/), [context length](https://docs.ollama.com/context-length),
  [graphics cards](https://docs.ollama.com/gpu), [FAQ](https://docs.ollama.com/faq) (settings such
  as `OLLAMA_CONTEXT_LENGTH` and `OLLAMA_NUM_PARALLEL`; its examples with `OLLAMA_HOST=0.0.0.0` open
  Ollama to the network: do not copy them).
- [Open WebUI documentation](https://docs.openwebui.com/).
- [NVIDIA: open GPU kernel modules](https://download.nvidia.com/XFree86/Linux-x86_64/580.95.05/README/kernel_open.html).

---

## About

This guide was made in the Erasmus+ project **Youth AI Lab**. Texts and templates are under
[CC BY-SA 4.0](LICENSES/CC-BY-SA-4.0.txt), configuration files under [EUPL-1.2](LICENSES/EUPL-1.2.txt);
details in `REUSE.toml`. Ollama, Open WebUI and the models belong to their authors.

Measured on 28 October 2026 with Ollama 0.40.8 and Open WebUI v0.11.4, on Ubuntu 26.04, on a Lenovo
ThinkPad P14s Gen 6 with an NVIDIA RTX PRO 500 (6 GB), with the 11 test questions of the workshop
kit.

For the measures, Open WebUI ran from its official Docker image. The installation of part 3 uses the
same version of Open WebUI, the same search model (`all-MiniLM-L6-v2`) and the same version of torch
(2.9.1, for the processor).

Checked on 28 October 2026 on another computer, under Ubuntu 26.04 (Python 3.14), through Open
WebUI's programming interface:

- the commands of part 3 as written, in an empty home folder (uv 0.13.1, Python 3.12 downloaded by
  uv, about 1 GB downloaded, 2.6 GB for `venv`), and Open WebUI started from the file of the
  service of step 5, as a service of the user rather than of the computer (no `sudo` on that
  computer, so without its line `User=`, and on port 3101), reachable from this computer only. The
  file of the service passes `systemd-analyze verify`;
- the deletion at the end of the project, in the same way: nothing left of Open WebUI, and 2.7 GiB
  freed by `uv cache clean`;
- the settings applied (banner, sessions of 12 hours, administrator's details hidden, sign-ups
  closed after the first account, Ollama only), the search model used without internet: the
  37 documents of the workshop indexed in 19 seconds, and the passages of the right documents
  found for a question;
- the sessions kept when Open WebUI starts again;
- with `GLOBAL_LOG_LEVEL=WARNING`, a sign-in leaves neither the e-mail nor the address in the
  journal (without it, both are there);
- with Open WebUI's Docker image of the same version and a tiny model (`qwen2.5:0.5b`): **Hide
  Model** then **Make Public** on the base model, and a participant account that reaches a
  **Public** chatbot, and also the hidden base model.

Followed on screen on 29 October 2026, on the laptop of the measures (Ubuntu 26.04, Python 3.14, an
older uv already installed, other models of Ollama already there), parts 1 to 6 of the previous
version of this guide. This version corrects what failed there: the model to choose in part 3,
step 7, and the safety net of the base model in part 6. What we saw:

- part 2: `OLLAMA_NO_CLOUD=1` in the service, `Ollama cloud disabled: true` in its journal, Ollama
  for this computer only (`127.0.0.1:11434`), `qwen2.5:7b` on the card (`100% GPU`, then
  `13%/87% CPU/GPU` with a context of 8192 once the chatbot was set up);
- part 3: Python 3.12 from uv (CPython 3.12.14), the installation in a little more than a minute,
  the service of the computer started with `sudo systemctl`, ready in 20 seconds, for this
  computer only; `.webui_secret_key` in `~/owui-local`; no e-mail and no address in the journal
  after the administrator's account was created;
- parts 4 and 5: a chatbot made from the filled example of `topic-assistant` and the summaries of
  the workshop, with **Legacy** and 8192: right answers with their sources in 5 to 6 seconds,
  "I don't know" for a city outside its documents;
- part 6, with a private window of the same computer at its network address instead of a phone:
  a participant account that sees only the chatbot, a right answer with its sources to a question
  in French, and the base model, reached with `?model=`, that answered "Please choose the group's
  chatbot in the list." to "Hello" once the three changes of its safety net were saved. With the
  System Prompt alone, it did not.

The new order of part 6, step 3 (safety net first, then **Hide Model** and **Make Public**) and
the line `ENABLE_EVALUATION_ARENA_MODELS=false` of [`openwebui.env`](openwebui.env) were not
followed on screen.

TO BE COMPLETED: follow them on a fresh installation, and part 6 with a real group, from phones on
the Wi-Fi.
