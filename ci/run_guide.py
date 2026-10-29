"""Runs the commands of the guide, as a reader would type them, and checks what they show.

The commands come from README.md itself: each code block to run has a marker just before it,
an HTML comment that GitHub does not show:

    <!-- ci linux stage=install check="uv --version" expect="uv 0.13.6" -->

- `linux` (or `macos`, `windows`): the version of the guide the block belongs to;
- `stage=`: the blocks of one stage run in order, in one shell, like one terminal;
- `check="..."`: a command the text asks the reader to type after the block ("What you should see");
- `expect="..."`: a text that the output of the block (and of its check) must contain.

A few changes are made to the commands, and only these (SUBSTITUTIONS below): the runners of CI
have no graphics card, so they use a much smaller model, and a pull request tests its own
openwebui.env rather than the one already published.

Usage: python3 ci/run_guide.py --os linux --stage install
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
MODEL = os.environ.get("CI_MODEL", "qwen2.5:0.5b")
SUBSTITUTIONS = [
    # No graphics card in CI: a 0.4 GB model instead of 4.7 GB, which would take minutes per answer.
    ("qwen2.5:7b", MODEL),
    # Test the settings of this commit, not those of the published guide.
    ("curl -fsSLO https://raw.githubusercontent.com/Youth-AI-Lab/yal-local-ai-guide/main/openwebui.env",
     f'cp "{ROOT}/openwebui.env" .'),
]
MARKER = re.compile(r"^\s*<!--\s*ci\s+(.*?)\s*-->\s*$")
FENCE = re.compile(r"^(\s*)```(\w+)\s*$")


def blocks(os_name, stage):
    """The marked blocks of README.md for this system and stage, in the order of the guide."""
    lines = README.read_text(encoding="utf-8").split("\n")
    found = []
    for i, line in enumerate(lines):
        m = MARKER.match(line)
        if not m or i + 1 >= len(lines):
            continue
        spec = m.group(1)
        systems = spec.split()[0].split(",")
        if os_name not in systems or f"stage={stage}" not in spec.split():
            continue
        fence = FENCE.match(lines[i + 1])
        if not fence:
            sys.exit(f"README.md line {i + 1}: a ci marker must be just before a code block")
        indent = fence.group(1)
        body, j = [], i + 2
        while not lines[j].strip().startswith("```"):
            body.append(lines[j][len(indent):] if lines[j].startswith(indent) else lines[j])
            j += 1
        code = "\n".join(body)
        for old, new in SUBSTITUTIONS:
            code = code.replace(old, new)
        found.append({
            "line": i + 2,
            "code": code,
            "checks": re.findall(r'check="([^"]*)"', spec),
            "expects": re.findall(r'expect="([^"]*)"', spec),
        })
    return found


def bash_script(found, out_dir):
    """One bash script: each block in a function, so that cd, export and source stay for the next one."""
    # A command that fails stops everything, as a reader would stop at an error.
    parts = ["set -eE -o pipefail", "trap 'echo \"::error::failed: $BASH_COMMAND\"' ERR"]
    for n, b in enumerate(found):
        out = out_dir / f"{n}.txt"
        checks = "\n".join(b["checks"])
        parts.append(f"block_{n}() {{\n{b['code']}\n}}")
        parts.append(f"check_{n}() {{\n{checks or ':'}\n}}")
        parts.append(
            f'echo "::group::README.md line {b["line"]}"\n'
            f"block_{n} > >(tee {out}) 2>&1; rc=$?\n"
            f"if [ $rc -eq 0 ]; then check_{n} > >(tee -a {out}) 2>&1; rc=$?; fi\n"
            f'sleep 1; echo "::endgroup::"\n'
            f'if [ $rc -ne 0 ]; then echo "::error::README.md line {b["line"]}: exit code $rc"; exit $rc; fi')
    return "\n\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--os", required=True, choices=["linux", "macos", "windows"])
    parser.add_argument("--stage", required=True)
    parser.add_argument("--print", action="store_true", help="show the script, do not run it")
    args = parser.parse_args()
    found = blocks(args.os, args.stage)
    if not found:
        sys.exit(f"no block marked for {args.os}, stage {args.stage}")
    if args.os == "windows":
        sys.exit("windows: not written yet")
    out_dir = Path(tempfile.mkdtemp(prefix="guide-"))
    script = out_dir / "guide.sh"
    script.write_text(bash_script(found, out_dir), encoding="utf-8")
    if args.print:
        print(script.read_text(encoding="utf-8"))
        return
    print(f"{len(found)} blocks of README.md, stage {args.stage}, model {MODEL}", flush=True)
    # A login shell, as a new terminal: it reads the profile that the installers change.
    rc = subprocess.run(["bash", "-l", str(script)], cwd=Path.home()).returncode
    if rc != 0:
        sys.exit(rc)
    failed = []
    for n, b in enumerate(found):
        text = (out_dir / f"{n}.txt").read_text(encoding="utf-8", errors="replace")
        for want in b["expects"]:
            if want not in text:
                failed.append(f'README.md line {b["line"]}: "{want}" not in the output')
    for f in failed:
        print(f"::error::{f}")
    if failed:
        sys.exit(1)
    print(f"stage {args.stage}: every block ran and showed what the guide says")


if __name__ == "__main__":
    main()
