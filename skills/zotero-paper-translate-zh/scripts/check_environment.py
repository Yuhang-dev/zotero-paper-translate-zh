# -*- coding: utf-8 -*-
"""Check the environment for the zotero-paper-translate-zh skill.

All paths, IDs and ports are discovered or user-supplied; nothing is
hard-coded to a specific machine.

Checks:
1. Python version (>= 3.9 recommended).
2. PyMuPDF availability (required for PDF body extraction).
3. Zotero Desktop running? Probed via the local Zotero connector port
   (default 23119, override with --zotero-port).
4. Zotero MCP / bridge availability: either the MCP port responds
   (default 23120, override with --mcp-port) or `zotero-cli` is on PATH.
5. Output directory writability, if provided via --workdir.

Usage:
    python check_environment.py [--zotero-port 23119] [--mcp-port 23120] [--workdir <dir>]
"""
import argparse
import importlib.util
import json
import os
import shutil
import socket
import sys

MIN_PYTHON = (3, 9)
DEFAULT_ZOTERO_PORT = 23119   # Zotero Connector HTTP API
DEFAULT_MCP_PORT = 23120      # Zotero MCP server (default; configurable)


def check_python():
    v = sys.version_info
    ok = (v.major, v.minor) >= MIN_PYTHON
    return ok, "%d.%d.%d (%s)" % (v.major, v.minor, v.micro, "OK" if ok else "too old, >= 3.9 recommended")


def check_pymupdf():
    spec = importlib.util.find_spec("pymupdf")
    if spec is None:
        return False, "NOT installed -- run: python -m pip install -r requirements.txt"
    try:
        import pymupdf
        return True, "installed, version %s" % pymupdf.__version__
    except Exception as exc:
        return False, "import failed: %s" % exc


def check_port(host, port, timeout=1.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_zotero_cli():
    path = shutil.which("zotero-cli")
    if path:
        return True, path
    return False, "not on PATH (optional; needed for attachment write-back)"


def main():
    parser = argparse.ArgumentParser(description="Check environment for zotero-paper-translate-zh")
    parser.add_argument("--zotero-port", type=int, default=DEFAULT_ZOTERO_PORT, help="Zotero connector port (default %d)" % DEFAULT_ZOTERO_PORT)
    parser.add_argument("--mcp-port", type=int, default=DEFAULT_MCP_PORT, help="Zotero MCP port (default %d)" % DEFAULT_MCP_PORT)
    parser.add_argument("--host", default="127.0.0.1", help="Zotero host (default 127.0.0.1)")
    parser.add_argument("--workdir", default=None, help="Output directory to check writability")
    args = parser.parse_args()

    results = {}
    results["python"] = check_python()
    results["pymupdf"] = check_pymupdf()

    zotero_up = check_port(args.host, args.zotero_port)
    results["zotero_desktop"] = (
        zotero_up,
        "running (port %d reachable)" % args.zotero_port
        if zotero_up
        else "not detected on port %d -- Zotero Desktop may be closed or port differs" % args.zotero_port,
    )

    mcp_up = check_port(args.host, args.mcp_port)
    cli_ok, cli_path = check_zotero_cli()
    if mcp_up:
        zotero_conn = "MCP reachable on port %d" % args.mcp_port
    elif cli_ok:
        zotero_conn = "no MCP on port %d, but zotero-cli found: %s" % (args.mcp_port, cli_path)
    else:
        zotero_conn = "no MCP on port %d and no zotero-cli on PATH" % args.mcp_port
    results["zotero_connector"] = (mcp_up or cli_ok, zotero_conn)

    if args.workdir:
        wdir = os.path.abspath(args.workdir)
        try:
            os.makedirs(wdir, exist_ok=True)
            probe = os.path.join(wdir, ".zotero_skill_write_probe")
            with open(probe, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(probe)
            results["workdir"] = (True, "writable: %s" % wdir)
        except OSError as exc:
            results["workdir"] = (False, "NOT writable: %s (%s)" % (wdir, exc))

    print(json.dumps(results, ensure_ascii=False, indent=2))

    required = [k for k, (ok, _) in results.items() if not ok]
    if required:
        print("\nMissing/blocked: %s" % ", ".join(required), file=sys.stderr)
        sys.exit(1)
    print("\nEnvironment OK.")


if __name__ == "__main__":
    main()
