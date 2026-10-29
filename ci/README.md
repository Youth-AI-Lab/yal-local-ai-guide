# The guide, followed by a machine

The workflow [`guide.yml`](../.github/workflows/guide.yml) follows this guide from start to end on
a fresh machine of GitHub, at each change and every Monday (the installers of Ollama and uv change
without us). The goal: each kind of computer the guide is written for can do it from start to end.

| System | State |
|---|---|
| Linux (Ubuntu 26.04, the system of the guide, and 24.04) | tested by the workflow |
| macOS | TO BE COMPLETED: the macOS version of parts 1 to 3, then its job |
| Windows | TO BE COMPLETED: the Windows version of parts 1 to 3, then its job |

## How it works

**The commands of the guide** run as they are written in [`README.md`](../README.md). A marker, an
HTML comment that GitHub does not show, says which code blocks to run, and what the reader should
see:

```html
<!-- ci linux stage=install check="uv --version" expect="uv 0.13.6" -->
```

- `linux`: the version of the guide this block belongs to (later also `macos`, `windows`);
- `stage=`: [`run_guide.py`](run_guide.py) runs the blocks of one stage in order, in one shell, as
  in one terminal: `install` (parts 2 and 3), `network` (part 6, before the first session),
  `delete` (the deletion at the end of the project);
- `check="..."`: a command that the text asks the reader to type after the block;
- `expect="..."`: a text that the output must contain ("What you should see").

Only two things change in the commands (`SUBSTITUTIONS` in `run_guide.py`): the machines of GitHub
have no graphics card, so the model is `qwen2.5:0.5b` instead of `qwen2.5:7b`, and a change tests its
own `openwebui.env` instead of the published one.

**What is done in the browser** (part 3 steps 6 and 7, parts 4 to 6) is done by
[`check_guide.py`](check_guide.py) through the programming interface of Open WebUI, with the same
settings as the guide: the administrator account, the settings of `openwebui.env`, a chatbot with
**Legacy** and **num_ctx 8192** on four summaries of the workshop kit, its sources, the safety net
of the base model, **Public** access, a participant account and what it sees, and no e-mail or
address in the journal.

## When you change the guide

- **A command**: change it in `README.md`; the workflow runs the new one. Keep the marker just before
  its code block.
- **A step in the browser** (parts 4 to 6): change `check_guide.py` too. It does not read the text of
  these parts.
- **A new block to run**: add a marker before it.

## What it does not check

The graphics card and its driver (part 1), the speed and the quality of the answers (a tiny model,
on a processor), the screens and their labels, and phones on a real Wi-Fi. Check these by hand on a
real computer, as in the [About](../README.md#about) section.
