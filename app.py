#!/usr/bin/env python3
# ------------------------------------------------------------
# QTAIM TOOLKIT (ORCA → Critic2 PIPELINE)
# Author: Ondřej Hasník
# Year: 2026
#
# Description:
#   CLI tool for quantum chemistry workflow:
#   ORCA .out → orca_2aim → .wfx → Critic2 QTAIM analysis
# ------------------------------------------------------------

"""
QTAIM Toolkit
=============

This script provides an automated workflow for Quantum Theory of Atoms
in Molecules (QTAIM) analysis.

Pipeline:
    1. ORCA output (.out) optionally converted via orca_2aim → .wfx
    2. Critic2 analysis (MOLECULE / LOAD / AUTO)
    3. Structured CLI output with ORCA-style formatting

Features:
    - ORCA-like logging and headers
    - Robust error handling with boxed messages
    - CLI interface (-w / -o)
    - Automatic file validation

Author: Ondřej Hasník
"""

import os
import sys
import socket
import argparse
import subprocess
from datetime import datetime
import textwrap


# ============================================================
# BANNER
# ============================================================
def banner(text_lines, padding=2):
    """
    Print ASCII banner with centered text and automatic wrapping.

    Parameters
    ----------
    text_lines : list[str]
        Lines to display in banner
    padding : int
        Horizontal padding inside box
    """

    wrapped = []
    max_width = 80  # safety width for terminal

    # wrap long lines to avoid overflow in terminal
    for line in text_lines:
        wrapped.extend(textwrap.wrap(line, width=max_width) or [""])

    width = max(len(line) for line in wrapped) + padding * 2

    top = "╔" + "═" * width + "╗"
    bottom = "╚" + "═" * width + "╝"

    print(top)
    for line in wrapped:
        print(
            "║"
            + " " * padding
            + line.center(width - padding * 2)
            + " " * padding
            + "║"
        )
    print(bottom)
    print()


# ============================================================
# HPC HEADER (ORCA STYLE)
# ============================================================
def print_header():
    """Print runtime environment information."""

    line = "*" * 35

    now = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
    host = socket.gethostname()
    pid = os.getpid()
    cwd = os.getcwd()

    print(line)
    print(f"* Starting time: {now}")
    print(f"* Host name:     {host}")
    print(f"* Process ID:    {pid}")
    print(f"* Working dir.:  {cwd}")
    print(line)
    print()


# ============================================================
# BOX UTILITIES
# ============================================================
def star_box(lines):
    """
    Print a simple ORCA-like star framed message box.
    """
    max_len = max(len(line) for line in lines)
    width = max_len + 4

    top = "*" * width

    print("\n" + top)
    for line in lines:
        print(f"* {line.ljust(max_len)} *")
    print(top + "\n")


def error_box(message):
    """
    Print standardized error message and terminate program.
    """
    star_box([
        "QTAIM INPUT ERROR",
        message,
        "QTAIM TERMINATED WITH ERROR"
    ])
    sys.exit(1)


def success_box():
    """
    Print successful termination message.
    """
    star_box([
        "QTAIM TERMINATED NORMALLY"
    ])


# ============================================================
# ORCA → WFX CONVERSION
# ============================================================
def run_orca_2aim(out_file):
    """
    Convert ORCA .out file to .wfx using orca_2aim.

    Parameters
    ----------
    out_file : str
        ORCA output file

    Returns
    -------
    str
        Generated .wfx file path
    """

    if not os.path.isfile(out_file):
        error_box(f"File not found: {out_file}")

    base = os.path.splitext(out_file)[0]

    print(f"[INFO] Running orca_2aim on: {out_file}")

    try:
        subprocess.run(["orca_2aim", base], check=True)
    except FileNotFoundError:
        error_box("orca_2aim not found in PATH.")
    except subprocess.CalledProcessError:
        error_box("orca_2aim execution failed.")

    wfx_file = base + ".wfx"

    if not os.path.isfile(wfx_file):
        error_box(f"Generated file not found: {wfx_file}")

    return wfx_file


# ============================================================
# CRITIC2 RUNNER
# ============================================================
def run_critic2(file_path):
    """
    Run Critic2 QTAIM analysis.

    Commands sent:
        MOLECULE file
        LOAD file
        AUTO
    """

    if not os.path.isfile(file_path):
        error_box(f"File not found: {file_path}")

    print(f"[INFO] Running Critic2 on: {file_path}\n")

    critic2_input = f"""MOLECULE {file_path}
LOAD {file_path}
AUTO
"""

    try:
        process = subprocess.Popen(
            ["critic2"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        output, _ = process.communicate(critic2_input)

        print(output)

        if process.returncode != 0:
            error_box(f"Critic2 exited with code {process.returncode}")

        success_box()

    except FileNotFoundError:
        error_box("Critic2 not found in PATH.")


# ============================================================
# ARGPARSE (CUSTOM ERROR STYLE)
# ============================================================
class QTAIMParser(argparse.ArgumentParser):
    """
    Custom ArgumentParser with ORCA-style error handling.
    """

    def error(self, message):
        error_box(message)


# ============================================================
# MAIN
# ============================================================
def main():
    """
    Entry point of QTAIM CLI tool.
    """

    parser = QTAIMParser(
        description="QTAIM toolkit: ORCA / Critic2 pipeline"
    )

    # mutually exclusive input modes
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-w", "--wfx", help="Input .wfx file")
    group.add_argument("-o", "--orca", help="Input ORCA .out file")

    args = parser.parse_args()

    # startup UI
    banner([
        "Quantum Theory of Atoms in Molecules (QTAIM) toolkit",
        "ORCA → Critic2 automated pipeline",
        "© 2026 Ondřej Hasník"
    ])

    print_header()

    # workflow selection
    if args.wfx:
        wfx_file = args.wfx

    elif args.orca:
        wfx_file = run_orca_2aim(args.orca)

    else:
        error_box("No valid input provided.")

    # run QTAIM analysis
    run_critic2(wfx_file)


if __name__ == "__main__":
    main()
