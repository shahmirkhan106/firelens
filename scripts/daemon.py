#!/usr/bin/env python3
"""Detach a command as a double-forked daemon and exit immediately.

Usage:  python scripts/daemon.py --log /path/log.log -- cmd args...
"""
import argparse
import os
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--log", required=True)
    p.add_argument("--cwd", default=None, help="working directory for the command")
    p.add_argument("--cmd", nargs=argparse.REMAINDER, required=True)
    args = p.parse_args()

    if "--" in args.cmd:
        args.cmd = args.cmd[args.cmd.index("--") + 1:]
    if not args.cmd:
        sys.exit("no command given")

    if args.cwd:
        os.chdir(args.cwd)

    if os.fork() > 0:
        return 0
    os.setsid()
    if os.fork() > 0:
        os._exit(0)

    devnull = os.open(os.devnull, os.O_RDONLY)
    logfd = os.open(args.log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    os.dup2(devnull, 0)
    os.dup2(logfd, 1)
    os.dup2(logfd, 2)
    for fd in (devnull, logfd):
        if fd > 2:
            os.close(fd)

    try:
        os.execvp(args.cmd[0], args.cmd)
    except Exception as e:
        with open(args.log, "a") as f:
            f.write(f"daemon failed: {e}\n")
        os._exit(1)


if __name__ == "__main__":
    main()