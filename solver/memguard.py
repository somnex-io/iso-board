#!/usr/bin/env python3
"""Run a command and SIGKILL it if its process tree's resident memory passes a cap.

macOS does not enforce `ulimit -v` / RLIMIT_AS (setrlimit fails), so this is the
OS-level backstop behind CP-SAT's own max_memory_in_mb. Polls every 0.5 s.

usage: memguard.py MAX_MB -- command args...
exit code: the command's, or 137 if killed for memory.
"""
import os, signal, subprocess, sys, time


def tree_rss_mb(root):
    out = subprocess.run(["ps", "-A", "-o", "pid=,ppid=,rss="], capture_output=True, text=True).stdout
    kids, rss = {}, {}
    for line in out.splitlines():
        pid, ppid, kb = map(int, line.split())
        kids.setdefault(ppid, []).append(pid); rss[pid] = kb
    total, stack = 0, [root]
    while stack:
        p = stack.pop(); total += rss.get(p, 0); stack += kids.get(p, [])
    return total / 1024


def main():
    cap = float(sys.argv[1]); cmd = sys.argv[sys.argv.index("--") + 1:]
    proc = subprocess.Popen(cmd, start_new_session=True)
    peak = 0.0
    try:
        while proc.poll() is None:
            mb = tree_rss_mb(proc.pid); peak = max(peak, mb)
            if mb > cap:
                os.killpg(proc.pid, signal.SIGKILL); proc.wait()
                print(f"memguard: KILLED at {mb:.0f} MB (cap {cap:.0f} MB)", file=sys.stderr, flush=True)
                sys.exit(137)
            time.sleep(0.5)
    except KeyboardInterrupt:
        os.killpg(proc.pid, signal.SIGKILL); raise
    print(f"memguard: peak {peak:.0f} MB (cap {cap:.0f} MB)", file=sys.stderr, flush=True)
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
