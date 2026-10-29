"""Starts Open WebUI with the settings of openwebui.env, on macOS and Windows.

On Linux, the service of the computer (systemd) does this job: see linux.md, part 3, step 5. macOS
(launchd) and Windows (Task Scheduler) have no equivalent of its line "EnvironmentFile=", so their
pages start this small program instead, with the Python of the virtual environment:

    macOS:    ~/owui-local/venv/bin/python ~/owui-local/owui-start.py 127.0.0.1
    Windows:  %USERPROFILE%\\owui-local\\venv\\Scripts\\pythonw.exe owui-start.py 127.0.0.1

It must sit in the folder of Open WebUI (owui-local), next to openwebui.env, venv and data. It:

1. reads openwebui.env as systemd reads an EnvironmentFile, for the kind of lines this file has:
   blank lines and lines starting with '#' or ';' are skipped, each other line is cut at its first
   '=', and a value that starts and ends with the same quote (" or ') loses these two quotes. Other
   quotes are kept as they are. With this rule, the 31 settings of openwebui.env come out the same
   as under systemd (checked with systemd-run), including WEBUI_BANNERS, whose JSON has quotes and an
   apostrophe. systemd reads backslashes, and some other quotes, in its own way: after adding a value
   with a backslash or a new quote to openwebui.env, compare again with systemd-run;
2. adds DATA_DIR (the folder of the data) and SENTENCE_TRANSFORMERS_HOME (the search model
   downloaded in part 3), as the service of linux.md does, unless they are already set;
3. starts "open-webui serve --host <address> --port 3000" from the virtual environment, in the
   folder owui-local, where Open WebUI keeps .webui_secret_key (the sign-ins survive a restart);
4. writes everything Open WebUI says in owui-local/open-webui.log. This file replaces the journal
   of Linux. It is also needed on Windows: started without a window (pythonw), Open WebUI has
   nowhere to write and stops at once;
5. ends with the exit code of Open WebUI, so that launchd (KeepAlive with SuccessfulExit false)
   starts it again only after a crash. For Task Scheduler (RestartCount), whether an exit code other
   than 0 counts as a failure is not tested.

The only argument is the address to listen on: 127.0.0.1 (this computer only, the default) or
0.0.0.0 (every network of the computer, part 6). Standard library only: Python 3.11 or newer.
"""
import os
import signal
import subprocess
import sys
from pathlib import Path

FOLDER = Path(__file__).resolve().parent  # owui-local
PORT = "3000"
WINDOWS = os.name == "nt"


def read_env_file(path):
    """The settings of an env file, read like systemd's EnvironmentFile (see point 1 above)."""
    settings = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        key, sep, value = line.partition("=")
        if not sep:  # a line without '=' is ignored, as systemd does
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]  # KEY="value" gives value, as under systemd
        settings[key.strip()] = value
    return settings


def keep_children_with_us():
    """Windows only: when this program is stopped, stop Open WebUI too.

    Task Scheduler stops a task by ending this program. Without this, Open WebUI (a child process,
    and its own Python behind it) would go on running and keep port 3000. A Windows "job object"
    with the flag KILL_ON_JOB_CLOSE ends every process in the job when the last handle to the job
    closes, that is when this program ends. This program joins the job before it starts Open WebUI,
    so that Open WebUI and the processes it starts join it too. If anything here fails, Open WebUI
    still starts (not tested on Windows).
    """
    import ctypes
    from ctypes import wintypes

    class BasicLimits(ctypes.Structure):  # JOBOBJECT_BASIC_LIMIT_INFORMATION
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", ctypes.c_uint32), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", ctypes.c_uint32),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", ctypes.c_uint32),
                    ("SchedulingClass", ctypes.c_uint32)]

    class IoCounters(ctypes.Structure):  # IO_COUNTERS
        _fields_ = [(name, ctypes.c_uint64) for name in (
            "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
            "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class ExtendedLimits(ctypes.Structure):  # JOBOBJECT_EXTENDED_LIMIT_INFORMATION
        _fields_ = [("BasicLimitInformation", BasicLimits), ("IoInfo", IoCounters),
                    ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    job = kernel32.CreateJobObjectW(None, None)
    limits = ExtendedLimits()
    limits.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    extended_limit_information = 9  # JobObjectExtendedLimitInformation
    if not (job and kernel32.SetInformationJobObject(wintypes.HANDLE(job), extended_limit_information,
                                                     ctypes.byref(limits), ctypes.sizeof(limits))
            and kernel32.AssignProcessToJobObject(wintypes.HANDLE(job),
                                                  wintypes.HANDLE(kernel32.GetCurrentProcess()))):
        raise OSError(ctypes.get_last_error(), "job object")
    return job  # keep the handle open as long as this program runs


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    log = open(FOLDER / "open-webui.log", "ab")  # append: the messages of earlier starts stay
    try:
        env = dict(os.environ)
        env.update(read_env_file(FOLDER / "openwebui.env"))
        env.setdefault("DATA_DIR", str(FOLDER / "data"))
        env.setdefault("SENTENCE_TRANSFORMERS_HOME", str(FOLDER / "data" / "cache" / "embedding" / "models"))
        # The log file in UTF-8 on every system (Windows would otherwise use its older code page).
        env.setdefault("PYTHONIOENCODING", "utf-8")
        # Every line in the log at once, for "tail -n 20" when something goes wrong.
        env.setdefault("PYTHONUNBUFFERED", "1")
        if WINDOWS:
            program = FOLDER / "venv" / "Scripts" / "open-webui.exe"
        else:
            program = FOLDER / "venv" / "bin" / "open-webui"
        options = {}
        job = None
        if WINDOWS:
            options["creationflags"] = subprocess.CREATE_NO_WINDOW  # no black window on the screen
            try:
                job = keep_children_with_us()  # the handle must stay open until the end
            except Exception as error:  # not fatal: Open WebUI still starts
                log.write(f"owui-start.py: no job object ({error})\n".encode())
        child = subprocess.Popen([str(program), "serve", "--host", host, "--port", PORT], cwd=FOLDER,
                                 env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                 **options)
    except Exception as error:
        # Under pythonw nobody sees an error on the screen: write it in the log.
        log.write(f"owui-start.py: cannot start Open WebUI: {error!r}\n".encode())
        log.close()
        return 1
    if not WINDOWS:
        # launchd stops a program with the signal TERM: pass it on to Open WebUI, and wait for it.
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, lambda number, frame: child.send_signal(number))
    code = child.wait()
    del job  # Windows: the job, kept until now, closes with this program
    log.close()
    # A program stopped by a signal has a negative code here; the shell's convention is 128 + signal.
    return 128 - code if code < 0 else code


if __name__ == "__main__":
    sys.exit(main())
