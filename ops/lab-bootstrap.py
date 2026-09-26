#!/usr/bin/env python3
"""Bootstrap a lab node over its serial console.

Why this exists: on vJunos 26.2 the config disk is attached and seen by both layers but
not applied (see lab-book/03-vjunos-recipe.md). This script does what the disk cannot:
waits for the console login prompt, logs in, writes the node's rendered
`config/juniper.conf` to the box, loads it, commits, and verifies.

Usage:
    python3 ops/lab-bootstrap.py --topology lab/topologies/day-00-smoke.toml --node sw1

It talks to the node's TCP console (127.0.0.1:4500+ordinal, see ops/lab-gen.py), so the
domain must be running and its console bound. Idempotent: applying the same config again
is a no-op commit.
"""
from __future__ import annotations

import argparse
import base64
import socket
import sys
import time
from pathlib import Path

import importlib.util

LAB_GEN_PATH = Path(__file__).resolve().parent / "lab-gen.py"
_spec = importlib.util.spec_from_file_location("lab_gen", LAB_GEN_PATH)
lab_gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lab_gen)

DEFAULT_TOPOLOGY = lab_gen.DEFAULT_TOPOLOGY
load_ssh_key_line = lab_gen.load_ssh_key_line
load_topology = lab_gen.load_topology
render_init_conf = lab_gen.render_init_conf

CONSOLE_BASE_PORT = 4500
LOGIN_MATRIX = [
    ("root", ""),
    ("root", "admin@123"),
    ("admin", "admin@123"),
]
PROMPT_CHARS = (b"#", b">")


def die(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


class Console:
    def __init__(self, port: int, timeout: float = 3.0):
        self.sock = socket.create_connection(("127.0.0.1", port), 5)
        self.sock.settimeout(timeout)

    def read(self, seconds: float) -> bytes:
        end = time.time() + seconds
        buf = b""
        while time.time() < end:
            try:
                chunk = self.sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
            except socket.timeout:
                pass
        return buf

    def send(self, line: str) -> None:
        self.sock.sendall(line.encode() + b"\r")

    def command(self, line: str, wait: float) -> bytes:
        self.send(line)
        time.sleep(wait)
        return self.read(2.0)

    def close(self) -> None:
        self.sock.close()


def login(console: Console) -> str:
    console.send("")
    seen = console.read(3.0)
    for user, password in LOGIN_MATRIX:
        if any(p in seen for p in PROMPT_CHARS):
            return user
        console.send(user)
        time.sleep(1.5)
        step = console.read(2.0)
        if b"assword" not in step and not any(p in step for p in PROMPT_CHARS):
            continue
        console.send(password)
        time.sleep(5.0)
        out = console.read(3.0)
        if any(p in out for p in PROMPT_CHARS):
            print(f"logged in as {user!r}")
            return user
    die("could not log in with the known lab credentials")


def write_config(console: Console, config: str) -> None:
    """Write the config line by line. Deliberately boring: the console is a pty and
    clever encodings have failed here (see lab-book/07-ops-notes.md). Paced, but read
    only once at the end — reading after every line spends minutes of wall clock."""
    lines = config.splitlines()
    for line in lines:
        if "'" in line:
            die("a config line contains a single quote; extend this writer's quoting first")
    console.send(": > /var/tmp/bootstrap.conf")
    time.sleep(0.5)
    for line in lines:
        console.send("echo '" + line + "' >> /var/tmp/bootstrap.conf")
        time.sleep(0.12)
    time.sleep(1.5)
    out = console.command("wc -l /var/tmp/bootstrap.conf; head -3 /var/tmp/bootstrap.conf", 4.0)
    print(out.decode(errors="replace")[-400:])
    if b"No such file" in out:
        die("failed to stage the bootstrap file on the node")


def commit(console: Console) -> None:
    for attempt in (1, 2):
        out = console.command(
            'cli -c "configure; load override /var/tmp/bootstrap.conf; commit and-quit"',
            45.0,
        )
        text = out.decode(errors="replace")
        print(text[-600:])
        if "commit complete" in text or "commit succeed" in text:
            return
        print(f"commit did not confirm (attempt {attempt})")
    die("commit failed twice")


def verify(console: Console, hostname: str) -> None:
    out = console.command(
        'cli -c "show configuration system | display set | match host-name"', 10.0
    )
    text = out.decode(errors="replace")
    print(text[-400:])
    if f"host-name {hostname}" not in text:
        die(f"verification failed: host-name {hostname} not found in committed config")
    print(f"verified: {hostname} is configured")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topology", default=str(DEFAULT_TOPOLOGY))
    parser.add_argument("--node", required=True)
    args = parser.parse_args()

    topo = load_topology(Path(args.topology).resolve())
    names = [n["name"] for n in topo["nodes"]]
    if args.node not in names:
        die(f"node {args.node!r} is not in {args.topology} (have: {', '.join(names)})")

    ordinal = names.index(args.node) + 1
    port = CONSOLE_BASE_PORT + ordinal
    node = next(n for n in topo["nodes"] if n["name"] == args.node)
    key_line, _ = load_ssh_key_line(topo["lab"])
    config = render_init_conf(node, topo["lab"], key_line)
    startup = node.get("startup_config")
    if startup:
        config += "\n" + (Path(args.topology).resolve().parent.parent.parent / startup).read_text()

    print(f"bootstrapping lab-{args.node} over console 127.0.0.1:{port}")
    console = Console(port)
    try:
        login(console)
        write_config(console, config)
        commit(console)
        verify(console, args.node)
    finally:
        console.close()


if __name__ == "__main__":
    main()
