#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Edit a macro contained in the kbd_macro_new table of an ObinsKit SQLITE db.

    This program makes a copy of the ObinsKit SQLITE database at the specified
    db_path, and operates on the copy until any changes are validated. It
    `SELECT`s the `macro_value` column of the row in the `kbd_macro_new` table that
    has the specified name `macro_name`.

    This `macro_value` is converted into a list of convenient namedtuples then
    dumped into a temporary file, preceded by a header containing editing
    instructions.

    The shell's EDITOR is spawned, opening this temp file. When the EDITOR process
    exits, its contents are converted back into the raw list expected by
    `macro_value`.

    If the new `macro_value` is valid, and `dry_run` is False, the row is written
    back out to the table using an SQLITE `UPDATE` command.

# My code currently transforms your `originalMap` into two separate map representations:
#
# 1. `keycodes_by_value`, which optimizes lookups using the integer keycode and
# 2. `keycodes_by_name`, which optimizes lookups using the string name.
#
# My app does the following:
#
# 1. reads in an existing `macro_value` (list of ints),
# 2. serializes it into more human-readable syntax,
# 3. dumps this into a tmp file,
# 4. opens the tmp file in your `EDITOR`, allowing manual mods, then
# 5. after detecting changes to the modified file, re-serializes the human-readable representation of the "macro events" back into the "list of ints" that can be used to `UPDATE` the `macro_value` column of the SQLITE db table corresponding to the macro being edited.
#
    Requirements:
        1. Must be using a recent version of ObinsKit that uses the new
           `kbd_macro_new` table/schema.
        2.
"""

import argparse
import difflib
import enum
import http.server
import logging
import os
import pathlib
import pprint
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import typing
import urllib
import webbrowser

from keycodes import keycodes_by_value, keycodes_by_name
print("keycodes_by_value:")
pprint.pprint(keycodes_by_value)
print("keycodes_by_name:")
pprint.pprint(keycodes_by_name)

class ObinsKitMacroItemKey(enum.Enum):
    """
    Enumerated values for first value in each ObinsKit Macro 3-tuple.

    TODO: confirm this reverse-engineered information
    Each ObinsKit macro consists of sequences of 3 8-bit ints.
    The first value is an event key, one of (1=keyUp, 2=keyDown, 3=wait).
    The 2nd and 3rd values denote the keycode or wait time:
      If 1st == (KeyUp/Down):
        2nd = keycode
        3rd ignored
      If 1st == Wait:
        Wait time = 2nd + 3rd * 256
    """
    KEY_UP = 1
    KEY_DOWN = 2
    WAIT = 3
    def __str__(self) -> str:
        return f"{self.name:8}"

    def to_int(self) -> int:
        return int(self.value)

class ObinsKitMacroItemTuple(typing.NamedTuple):
    key: ObinsKitMacroItemKey
    value_2: int
    value_3: int

    def __repr__(self) -> str:
        """Detailed string repr of an ObinsKitMacroItemTuple used for debugging."""
        s = f'ObinsKitMacroItemTuple: key={ObinsKitMacroItemKey(self.key):8}'
        if ObinsKitMacroItemKey(self.key) in [ObinsKitMacroItemKey.KEY_UP, ObinsKitMacroItemKey.KEY_DOWN]:
            s += f' value_2={self.value_2:3} (keycode={keycodes_by_value[self.value_2]["name"]})'
        else:
            s += f' value_2={self.value_2:3} value_3={self.value_3:3} (wait={self.value_2 + self.value_3 * 256})'
        return s

    def __str__(self) -> str:
        """Simple string repr of an ObinsKitMacroItemTuple used in human-editable file."""
        s = f'{ObinsKitMacroItemKey(self.key):8}'
        if ObinsKitMacroItemKey(self.key) in [ObinsKitMacroItemKey.KEY_UP, ObinsKitMacroItemKey.KEY_DOWN]:
            s += f' {keycodes_by_value[self.value_2]["name"]}'
        else:
            s += f' {self.value_2 + self.value_3 * 256}'
        return s

    def from_str(strepr):
        """Convert a string repr of an ObinsKitMacroItemTuple to an ObinsKitMacroItemTuple."""
        logger.debug(f"from_str: '{strepr.strip()}'")
        key, value = strepr.strip().split()
        if key.upper() == "KEY_UP":
            return ObinsKitMacroItemTuple(ObinsKitMacroItemKey.KEY_UP, keycodes_by_name[value]['value'], 0)
        elif key.upper() == "KEY_DOWN":
            return ObinsKitMacroItemTuple(ObinsKitMacroItemKey.KEY_DOWN, keycodes_by_name[value]['value'], 0)
        elif key.upper() == "WAIT":
            return ObinsKitMacroItemTuple(ObinsKitMacroItemKey.WAIT, int(value), 0)

    def to_int_macro_value_list(self):
        """Convert this object into the 3 int list used by macro_value in SQLITE db."""
        return [self.key.to_int(), self.value_2, self.value_3]


def main(db_path, macro_name, dry_run=False):
    """
    """
    tmp_db_dir = tempfile.mkdtemp(prefix=str(db_path).replace(os.path.sep, '_') + '-')
    tmp_db_path = os.path.join(tmp_db_dir, os.path.basename(db_path))
    shutil.copyfile(db_path, tmp_db_path)
    logger.debug(f"Copied SQLITE db at path '{db_path}' to temp path '{tmp_db_path}'.")
    logger.debug(f"Connecting to SQLITE db at path '{tmp_db_path}'...")
    connection = sqlite3.connect(tmp_db_path)
    logger.debug(f"Getting a cursor from SQLITE db connection...")
    cursor = connection.cursor()
    # could LIMIT cmd to only SELECT 1, but let's assert instead
    cmd = f"SELECT macro_value FROM kbd_macro_new WHERE name='{macro_name}'"
    logger.debug(f"SELECTing macro_value with command {cmd}")
    cursor.execute(cmd)
    selections = cursor.fetchall()
    assert(len(selections) == 1,
        f"{len(selections)} rows were SELECTed by cmd '{cmd}'."
        f" There must be exactly one selected row."
        f" Check your SELECT command.")
    logger.debug(f'There are {len(selections)} items returned by cursor.fetch_all:\n{selections}')
    macro_value = selections[0][0].strip('[]').split(',')
    int_macro_value = [int(x) for x in macro_value]
    int_3_tuples = [tuple(int_macro_value[i:i+3]) for i in range(0, len(int_macro_value), 3)]
    logger.debug(f'There are {len(int_3_tuples)} 3-tuples in our modified macro_value list:\n{int_3_tuples}')
    fd, temppath = tempfile.mkstemp(text=True)
    with os.fdopen(fd, 'w') as f:
        logger.debug(f"Writing instructions to header in temp file {temppath}...")
        instructions = \
'''# INSTRUCTIONS FOR EDITING THIS OBINSKIT MACRO
#
# Change existing event values, or add new events, noting:
#   1. One event per line
#   2. Each event has 2 tokens separated by whitespace:
#      1. One of:
#         1. KEY_DOWN
#         2. KEY_UP
#         3. WAIT
#      2. Either a keycode for a KEY_* event, or a time in msec for a WAIT event.
#   3. Lines beginning with # are ignored (treated as comments).
# Example: Press J for 10msec before letting go.
#   KEY_DOWN J
#   WAIT     10
#   KEY_UP   J
'''
        f.write(instructions)
        logger.debug(f"Dumping macro events to temporary file {temppath} for editing...")
        for i,t in enumerate(map(ObinsKitMacroItemTuple._make, int_3_tuples)):
            logger.debug(f"{i:3}: {t}")
            f.write(f"{t}\n")
    # Open temp file in EDITOR
    cmd = f"{os.environ['EDITOR']} {temppath}"
    completed_process = subprocess.run(cmd, shell=True)
    logger.debug(f"Return code: {completed_process.returncode}")
    if completed_process.returncode != 0:
        logger.error(f"Editor process {os.environ['EDITOR']} returned error {completed_process.returncode}!")
        sys.exit(-1)
    # On successful return code, validate file (stripping comments and whitespace-only lines)
    # and re-encode macro_value and UPDATE table
    with open(temppath, 'r') as f:
        lines = [line for line in f.readlines() if (not line.startswith('#') and not line.isspace())]
    logger.debug(f"lines:\n{''.join(lines)}")
    new_macro_value = []
    for line in lines:
        new_macro_value += ObinsKitMacroItemTuple.from_str(line).to_int_macro_value_list()
    logger.debug(f"new_macro_value: {new_macro_value}")
    logger.debug(f"old_macro_value: {int_macro_value}")
    if new_macro_value == int_macro_value:
        logger.info("Macro Int Value not changed, nothing to update. Exiting..")
        sys.exit(0)

    # Print various diffs between old and new macro value lists
    # difference = list(set(macro_value) - set(new_macro_value))
    # logger.info(f"Difference between old and new macro_values is:\n{difference}")
    # symmetrical_difference = list(set(macro_value).symmetric_difference(set(new_macro_value)))
    # logger.info(f"Symmetrical Difference between old and new macro_values is:\n{symmetrical_difference}")
    old_strings = [f"{t}" for t in int_3_tuples]
    new_int_3_tuples = [tuple(new_macro_value[i:i+3]) for i in range(0, len(new_macro_value), 3)]
    new_strings = [f"{t}" for t in new_int_3_tuples]
    t0 = time.time()
    result = list(difflib.unified_diff(new_strings, old_strings, lineterm=''))
    logger.info(f"Text unified-diff between old and new macro_values (took {time.time()-t0}s):\n{pprint.pformat(result)}")
    t0 = time.time()
    html_str = difflib.HtmlDiff().make_file(old_strings, new_strings, fromdesc='old macro_values', todesc='new macro_values', context=True, numlines=5)
    html_dir = tempfile.mkdtemp()
    html_file_path = os.path.join(html_dir, 'index.html')
    with open(html_file_path, 'w') as f:
        f.write(html_str)
    logger.info(f"HTML diff between old and new macro_values (took {time.time()-t0:6.3}s, html_file_path={html_file_path}):\n{html_str}")

    logger.info(f"Opening HTML diff in browser...")
    wsl_path_prefix = "file://///wsl$/Debian"
    p = subprocess.Popen(["/mnt/c/Program Files/Firefox Nightly/firefox.exe", f"{wsl_path_prefix}{html_file_path}"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # required to detach sub from parent
    # rely on user to manage browser process(es), i.e. do not terminate

    # Webbrowser module doesn't seem to work on WSL.
    # ret = webbrowser.open(f"{html_file_path}")
    # logger.info(f"webbrowser.open returned {ret}...")

    # Webserver is unnecessary for viewing simple static local html file.
    # address = "127.0.0.1"
    # port = 8000
    # logger.info(f"Starting HTTP server to serve generated HTML...")
    # p = subprocess.Popen(["python", "-m", "http.server", f"{port}",
    #     "--bind", f"{address}", "--directory", f"{html_dir}"])
    # logger.info(f"Opening HTML diff in browser...")
    # # poll webserver until content retrieved.
    # while not urllib.request.urlopen(f"{address}:{port}"):
    #     time.sleep(0.25)
    # webbrowser.open_new(f"{address}:{port}")
    # # kill webserver
    # p.terminate()
    # p.wait()

    # UPDATE the macro_value column in the macro_name row in the kbd_macro_new table.
    cmd = f"UPDATE kbd_macro_new SET macro_value='{new_macro_value}' WHERE name='{macro_name}'"
    if not dry_run:
        logger.debug(f"UPDATEing macro_value with command {cmd}")
        cursor.execute(cmd)
    else:
        logger.debug(f"Dry-run! Would UPDATE macro_value with command {cmd}")

    # Commit any pending transaction to the database and close connection to it
    connection.commit()
    connection.close()
    logger.debug(f"Committed SQLITE transactions and closed connection.")
    logger.debug(f"Done! Now you should be able to see your changes by copying the"
            " temp SQLITE db file {tmp_db_path} to the default location for ObinsKit"
            " on your platform, e.g. on Windows it's"
            " /mnt/c/Users/876738897/AppData/Roaming/ObinsKit/Run.core.")


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    logger = logging.getLogger(os.path.splitext(__file__)[0])
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--db-path",
            required=True,
            action='store',
            type=pathlib.Path,
            help="Absolute path to local SQLITE database file")
    argparser.add_argument("--macro-name",
            required=True,
            action='store',
            type=str,
            help="Name of macro to edit. Use `SELECT name FROM kbd_macro_new` to list all macro names")
    argparser.add_argument("--dry-run",
            action='store_true',
            help="When True, don't write changes to sqlite database.")
    args = argparser.parse_args()
    main(args.db_path, args.macro_name, dry_run=args.dry_run)
