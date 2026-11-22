"""Locate a bash executable portably (Git Bash on Windows, system bash elsewhere).

Order: BASH_EXE env var, Git for Windows locations (Windows only, to avoid the
WSL launcher in System32), then `bash` on PATH.
"""
import os
import shutil
import sys


def find_bash():
    override = os.environ.get("BASH_EXE")
    if override:
        return override
    if sys.platform == "win32":
        candidates = [
            os.path.join(os.environ.get(var, ""), "Git", "bin", "bash.exe")
            for var in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA")
        ]
        candidates.append(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Git", "bin", "bash.exe"))
        git = shutil.which("git")
        if git:
            root = os.path.dirname(os.path.dirname(git))
            candidates.append(os.path.join(root, "bin", "bash.exe"))
        for path in candidates:
            if os.path.isfile(path):
                return path.replace("\\", "/")
    found = shutil.which("bash")
    if found:
        return found
    raise RuntimeError("bash not found; install Git Bash or set BASH_EXE")


BASH = find_bash()
