"""Runs the commands of the guide, as a reader would type them, and checks what they show.

The commands come from the pages of the guide themselves: README.md (what every system shares),
then the page of the system (linux.md, macos.md, windows.md or raspberry-pi.md). Each code block to
run has a marker just before it, an HTML comment that GitHub does not show:

    <!-- ci linux stage=install check="uv --version" expect="uv 0.13.6" -->

- `linux` (or `macos`, `windows`, `raspberry-pi`, `raspberry-pi-hat`, or several: `linux,macos`):
  the systems this block is for. `raspberry-pi` is the Raspberry Pi with the model on its processor
  (Ollama); `raspberry-pi-hat` is the same page with the AI HAT+ 2 (hailo-ollama). Both read
  raspberry-pi.md (PAGE below), and each takes only the blocks marked for it;
- `stage=`: the blocks of one stage run in order, in one shell, like one terminal;
- `check="..."`: a command the text asks the reader to type after the block ("What you should see");
- `expect="..."`: a text that the output of the block (and of its check) must contain.

The shell is the one of a reader of this system: bash on Linux and on Raspberry Pi OS, zsh (the
shell of the Terminal app) on macOS, Windows PowerShell 5.1 (the one that comes with Windows) on
Windows.

A few changes are made to the commands, and only these (SUBSTITUTIONS, hat_substitutions() and
DOWNLOAD below): the runners of CI have no graphics card, so they use a much smaller model (also in
place of the model of the Raspberry Pi page); on macOS, nobody can answer the window that asks
whether to open Ollama the first time, so CI removes the mark that makes macOS ask; GitHub has no
AI HAT+ 2, so for raspberry-pi-hat the service of hailo-ollama starts ci/fake_hailo_ollama.py, a
stand-in that answers like hailo-ollama 5.1.1, in place of /usr/bin/hailo-ollama (the real package
is still downloaded, checked, installed and removed); and a change of the guide tests its own
openwebui.env and owui-start.py rather than the ones already published.

Usage: python3 ci/run_guide.py --os linux --stage install [--print]
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.environ.get("CI_MODEL", "qwen2.5:0.5b")
SUBSTITUTIONS = [
    # No graphics card in CI: a 0.4 GB model instead of 4.7 GB, which would take minutes per answer.
    ("qwen2.5:7b", MODEL),
    # No Raspberry Pi in CI: the model of the Raspberry Pi page (processor route) becomes the same
    # tiny one. qwen2:1.5b, the model of the AI HAT+ 2, is not changed: the stand-in for
    # hailo-ollama serves the real list of models of the hailo-ollama 5.1.1 package.
    ("qwen2.5:1.5b", MODEL),
    # macOS CI: nobody can click Open in the Gatekeeper dialog of a quarantined app (the reader
    # does, macos.md part 2, step 2). Without this, the wait for Ollama would last until the timeout.
    ("open /Applications/Ollama.app --args hidden",
     "xattr -dr com.apple.quarantine /Applications/Ollama.app 2>/dev/null || true; "
     "open /Applications/Ollama.app --args hidden"),
]
# Test the files of this commit, not those of the published guide: a download of openwebui.env or
# owui-start.py, written exactly like this in the guide (curl on Linux and macOS, curl.exe in
# Windows PowerShell), becomes a copy from the checkout.
DOWNLOAD = re.compile(r"curl(?:\.exe)? -fsSLO https://raw\.githubusercontent\.com/Youth-AI-Lab/"
                      r"yal-local-ai-guide/main/(openwebui\.env|owui-start\.py)")
MARKER = re.compile(r"^\s*<!--\s*ci\s+(.*?)\s*-->\s*$")
FENCE = re.compile(r"^(\s*)```(\w+)\s*$")
# The page of each system, when it is not named after the system: the two routes of the Raspberry
# Pi page (processor, AI HAT+ 2) are two systems of CI, with their own markers, on one page.
PAGE = {"raspberry-pi-hat": "raspberry-pi"}
# The line of raspberry-pi.md (AI HAT+ 2, step 5) that starts hailo-ollama in its service.
HAILO_EXEC = "ExecStart=/usr/bin/hailo-ollama"
# The program that runs the PowerShell harness. Only for a test of this script on a computer
# without Windows PowerShell (for example CI_POWERSHELL=pwsh): the CI of the guide never sets it.
POWERSHELL = os.environ.get("CI_POWERSHELL", "powershell.exe")


def pages(os_name):
    """The pages read for this system, in this order."""
    return [p for p in (ROOT / "README.md", ROOT / f"{PAGE.get(os_name, os_name)}.md") if p.exists()]


def hat_substitutions(placeholders=False):
    """raspberry-pi-hat only: the service of hailo-ollama starts the stand-in of CI instead.

    GitHub has no AI HAT+ 2, and the real /usr/bin/hailo-ollama needs HailoRT and the chip. The rest
    of the service stays as the page writes it (User=, Environment=, StandardOutput=null, Restart=),
    and the stand-in reads /etc/xdg/hailo-ollama/hailo-ollama.json as hailo-ollama 5.1.1 does: the sed of the
    page decides where it listens. The paths come from the job (guide.yml). With --print and no
    job, placeholders show where they go.
    """
    names = ("CI_HAILO_FAKE_PYTHON", "CI_HAILO_LOG", "CI_QWEN2_TOKENIZER")
    values = [os.environ.get(n) or (f"<{n}>" if placeholders else None) for n in names]
    if not all(values):
        sys.exit("raspberry-pi-hat needs CI_HAILO_FAKE_PYTHON, CI_HAILO_LOG and CI_QWEN2_TOKENIZER (see guide.yml)")
    py, log, tok = values
    return [(HAILO_EXEC, f"ExecStart={py} -I {ROOT}/ci/fake_hailo_ollama.py --log {log} --tokenizer {tok}")]


def copy_command(os_name, name):
    if os_name == "windows":
        return f"Copy-Item -LiteralPath '{ROOT / name}' -Destination ."
    return f'cp "{ROOT}/{name}" .'


def blocks(os_name, stage, placeholders=False):
    """The marked blocks of the pages for this system and stage, in the order of the guide."""
    found = []
    substitutions = SUBSTITUTIONS
    if os_name == "raspberry-pi-hat":
        substitutions = SUBSTITUTIONS + hat_substitutions(placeholders)
    hailo_exec_seen = False
    for page in pages(os_name):
        lines = page.read_text(encoding="utf-8").split("\n")
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
                sys.exit(f"{page.name} line {i + 1}: a ci marker must be just before a code block")
            indent = fence.group(1)
            body, j = [], i + 2
            while not lines[j].strip().startswith("```"):
                body.append(lines[j][len(indent):] if lines[j].startswith(indent) else lines[j])
                j += 1
            code = "\n".join(body)
            hailo_exec_seen = hailo_exec_seen or HAILO_EXEC in code
            for old, new in substitutions:
                code = code.replace(old, new)
            code = DOWNLOAD.sub(lambda d: copy_command(os_name, d.group(1)), code)
            found.append({
                "where": f"{page.name} line {i + 2}",
                "code": code,
                "checks": re.findall(r'check="([^"]*)"', spec),
                "expects": re.findall(r'expect="([^"]*)"', spec),
            })
    if os_name == "raspberry-pi-hat" and stage == "install" and not hailo_exec_seen:
        # Otherwise the real hailo-ollama would start without its chip, and the stand-in never.
        sys.exit(f"raspberry-pi.md no longer starts hailo-ollama with {HAILO_EXEC}: update run_guide.py")
    return found


def bash_script(found, out_dir):
    """One bash script: each block in a function, so that cd, export and source stay for the next one."""
    # A command that fails stops everything, as a reader would stop at an error.
    parts = ["set -eE -o pipefail", "trap 'echo \"::error::failed: $BASH_COMMAND\"' ERR"]
    return "\n\n".join(parts + functions_and_calls(found, out_dir)) + "\n"


def zsh_script(found, out_dir):
    """The same for macOS, in zsh: the shell of the Terminal app, where the reader types."""
    parts = ["set -e -o pipefail", "trap 'echo \"::error::failed: exit code $?\"' ZERR"]
    return "\n\n".join(parts + functions_and_calls(found, out_dir)) + "\n"


def functions_and_calls(found, out_dir):
    parts = []
    for n, b in enumerate(found):
        out = out_dir / f"{n}.txt"
        checks = "\n".join(b["checks"])
        parts.append(f"block_{n}() {{\n{b['code']}\n}}")
        parts.append(f"check_{n}() {{\n{checks or ':'}\n}}")
        parts.append(
            f'echo "::group::{b["where"]}"\n'
            f"block_{n} > >(tee {out}) 2>&1; rc=$?\n"
            f"if [ $rc -eq 0 ]; then check_{n} > >(tee -a {out}) 2>&1; rc=$?; fi\n"
            f'sleep 1; echo "::endgroup::"\n'
            f'if [ $rc -ne 0 ]; then echo "::error::{b["where"]}: exit code $rc"; exit $rc; fi')
    return parts


def ps_string(text):
    """A PowerShell string that keeps the text as it is: a single-quoted here-string."""
    if any(line.startswith("'@") for line in text.split("\n")):
        sys.exit("a line of a Windows block starts with '@: it cannot be put in the harness")
    return "@'\n" + text + "\n'@"


def powershell_script(found, out_dir):
    """One Windows PowerShell 5.1 script, as one PowerShell window of a reader.

    Each top-level command of a block is dot-sourced (. { ... }) in the scope of the script, so that
    Set-Location, $env: and the variables of a block stay for the next one, as in one window. What
    it shows is printed and saved in a file, for the "expect" texts.

    The first error stops everything, as a reader would stop:
    - a command of PowerShell that writes an error, or throws one;
    - a program (uv, ollama, curl.exe...) that ends with an exit code other than 0 ($LASTEXITCODE).
    The commands run with $ErrorActionPreference 'Continue', the value of a reader's window, and the
    harness checks the errors after each command. With 'Stop', Windows PowerShell 5.1 would stop at
    the first line that a program writes on its error output when this output is captured, and uv
    or ollama write their progress there: the guide would fail where a reader sees no error.
    """
    head = [
        # The runners of GitHub allow every script (policy Unrestricted for the machine). A new
        # Windows 11 PC does not: its policy is Restricted, which blocks every script file (.ps1),
        # Activate.ps1 of a virtual environment included. The scope Process wins over the scope of
        # the machine, for this process and the programs it starts: the guide's blocks run under
        # the policy of a new PC. This file itself was started with -ExecutionPolicy Bypass, which
        # applies only to it.
        "Set-ExecutionPolicy -Scope Process -ExecutionPolicy Restricted -Force",
        "$ErrorActionPreference = 'Continue'",
        # A new PowerShell window takes its PATH from the settings of Windows, where installers
        # (Ollama, uv) add their folder: do the same, keeping what the runner already has.
        "$env:Path = (@([Environment]::GetEnvironmentVariable('Path', 'Machine'),"
        " [Environment]::GetEnvironmentVariable('Path', 'User'), $env:Path) -ne $null) -join ';'",
        "Set-Location $HOME",
        "$ciUtf8 = New-Object System.Text.UTF8Encoding $false",
        "function Show-CiItem($item) {",
        "  # A line written by a program on its error output is not an error by itself.",
        "  if ($item -is [System.Management.Automation.ErrorRecord]) { return $item.ToString() }",
        "  if ($item -is [string]) { return $item }",
        "  return ($item | Out-String -Width 200).TrimEnd()",
        "}",
        "function Test-CiFailed($item) {",
        "  ($item -is [System.Management.Automation.ErrorRecord]) -and"
        " ($item.FullyQualifiedErrorId -notlike 'NativeCommandError*')",
        "}",
    ]
    # The blocks of the guide, as they are written (after SUBSTITUTIONS and DOWNLOAD).
    data = []
    for n, b in enumerate(found):
        out = str(out_dir / f"{n}.txt").replace("'", "''")
        data.append(f"""  @{{where = '{b["where"]}'; out = '{out}'
    block = {ps_string(b["code"])}
    check = {ps_string(chr(10).join(b["checks"]))}
  }}""")
    loop = """
foreach ($ciBlock in $ciBlocks) {
  Write-Host "::group::$($ciBlock.where)"
  $ciFailed = $null
  foreach ($ciPart in @($ciBlock.block, $ciBlock.check)) {
    $ciTokens = $null; $ciParseErrors = $null
    $ciAst = [System.Management.Automation.Language.Parser]::ParseInput($ciPart, [ref]$ciTokens, [ref]$ciParseErrors)
    if ($ciParseErrors.Count -gt 0) { $ciFailed = "cannot read it: $($ciParseErrors[0].Message)"; break }
    # One command at a time, in the scope of this script (a reader's block should not use break,
    # continue or exit at its top level: they would act on these loops).
    foreach ($ciStatement in $ciAst.EndBlock.Statements) {
      $global:LASTEXITCODE = 0
      $ciLines = New-Object System.Collections.Generic.List[string]
      try {
        . ([scriptblock]::Create($ciStatement.Extent.Text)) *>&1 | ForEach-Object {
          $ciText = Show-CiItem $_
          Write-Host $ciText
          $ciLines.Add($ciText)
          if (-not $ciFailed -and (Test-CiFailed $_)) { $ciFailed = "error: $ciText" }
        }
      } catch {
        $ciText = $_.ToString()
        Write-Host $ciText
        $ciLines.Add($ciText)
        $ciFailed = "error: $ciText"
      }
      [System.IO.File]::AppendAllText($ciBlock.out, ($ciLines -join "`n") + "`n", $ciUtf8)
      if (-not $ciFailed -and $LASTEXITCODE -ne 0) { $ciFailed = "exit code $LASTEXITCODE" }
      if ($ciFailed) { $ciFailed = "$ciFailed, in: $($ciStatement.Extent.Text)"; break }
    }
    if ($ciFailed) { break }
  }
  Start-Sleep -Seconds 1
  Write-Host '::endgroup::'
  if ($ciFailed) { Write-Host "::error::$($ciBlock.where): $ciFailed"; exit 1 }
}
exit 0
"""
    return "\n".join(head) + "\n\n$ciBlocks = @(\n" + ",\n".join(data) + "\n)\n" + loop


def main():
    parser = argparse.ArgumentParser()
    # raspberry-pi and raspberry-pi-hat run in bash, as linux: Raspberry Pi OS has bash and systemd.
    parser.add_argument("--os", required=True,
                        choices=["linux", "macos", "windows", "raspberry-pi", "raspberry-pi-hat"])
    parser.add_argument("--stage", required=True)
    parser.add_argument("--print", action="store_true", help="show the script, do not run it")
    args = parser.parse_args()
    found = blocks(args.os, args.stage, placeholders=args.print)
    if not found:
        names = ", ".join(p.name for p in pages(args.os))
        sys.exit(f"no block marked for {args.os}, stage {args.stage} (in {names})")
    out_dir = Path(tempfile.mkdtemp(prefix="guide-"))
    if args.os == "windows":
        script = out_dir / "guide.ps1"
        # With a BOM, Windows PowerShell 5.1 reads the file as UTF-8 (without, in the old code page).
        script.write_text(powershell_script(found, out_dir), encoding="utf-8-sig")
        # -NoProfile: no profile of the runner. -ExecutionPolicy Bypass: lets this harness run;
        # its first line puts back the policy of a new PC for the guide's commands.
        command = [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script)]
    elif args.os == "macos":
        script = out_dir / "guide.zsh"
        script.write_text(zsh_script(found, out_dir), encoding="utf-8")
        # A login shell, as a new window of Terminal: it reads the files that the installers change.
        command = ["zsh", "-l", str(script)]
    else:
        script = out_dir / "guide.sh"
        script.write_text(bash_script(found, out_dir), encoding="utf-8")
        # A login shell, as a new terminal: it reads the profile that the installers change.
        command = ["bash", "-l", str(script)]
    if args.print:
        print(script.read_text(encoding="utf-8-sig"))
        shutil.rmtree(out_dir)
        return
    pages_read = " and ".join(p.name for p in pages(args.os))
    print(f"{len(found)} blocks of {pages_read}, stage {args.stage}, model {MODEL}", flush=True)
    rc = subprocess.run(command, cwd=Path.home()).returncode
    if rc != 0:
        sys.exit(rc)
    failed = []
    for n, b in enumerate(found):
        text = (out_dir / f"{n}.txt").read_text(encoding="utf-8", errors="replace")
        for want in b["expects"]:
            if want not in text:
                failed.append(f'{b["where"]}: "{want}" not in the output')
    for f in failed:
        print(f"::error::{f}")
    if failed:
        sys.exit(1)
    print(f"stage {args.stage}: every block ran and showed what the guide says")


if __name__ == "__main__":
    main()
