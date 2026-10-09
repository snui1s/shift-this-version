#!/usr/bin/env python3
"""Record REAL command output (run in a pty) into an asciicast v2 file.

Only the typing of each command is simulated (so it looks natural); everything the
commands print, including the AI call, is captured as-is with its real timing.
"""
import fcntl, json, os, pty, select, struct, sys, termios, time

COLS, ROWS = 100, 40
COMMANDS = [
    ("git log --oneline", 2.5),
    ("shift-this-version shift -y --no-push", 7.0),
    ("git log --oneline --decorate", 4.0),
]
PROMPT = "\x1b[1;32m$\x1b[0m "
events, t0 = [], time.time()


def emit(data):
    events.append([round(time.time() - t0, 4), "o", data])


def pause(sec):
    time.sleep(sec)


def type_command(cmd):
    emit(PROMPT)
    for ch in cmd:
        pause(0.04)
        emit(ch)
    pause(0.3)
    emit("\r\n")


def run_in_pty(cmd):
    pid, fd = pty.fork()
    if pid == 0:
        os.environ.update(TERM="xterm-256color", COLUMNS=str(COLS), LINES=str(ROWS), GIT_PAGER="cat")
        os.execvp("bash", ["bash", "-c", cmd])
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
    while True:
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            try:
                data = os.read(fd, 65536)
            except OSError:
                break
            if not data:
                break
            emit(data.decode("utf-8", "replace"))
    _, status = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(status)


failed = False
for cmd, hold in COMMANDS:
    type_command(cmd)
    if run_in_pty(cmd) != 0:
        failed = True
    pause(hold)
    emit("[2J[H")  # clear between scenes so each one fits on screen
emit(PROMPT)
pause(1.5)

out = sys.argv[1] if len(sys.argv) > 1 else "demo.cast"
with open(out, "w", encoding="utf-8") as f:
    f.write(json.dumps({"version": 2, "width": COLS, "height": ROWS,
                        "env": {"TERM": "xterm-256color"}}) + "\n")
    for e in events:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
sys.exit(1 if failed else 0)
