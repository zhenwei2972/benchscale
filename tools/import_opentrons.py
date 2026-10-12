"""Rebuild the cached Opentrons reference catalogue (downloads it if needed).

The Opentrons definitions are no longer bundled; see src/benchscale/thirdparty.py.
To move to a newer upstream commit, edit "commit" in src/benchscale/data/thirdparty.json.
Run:  python tools/import_opentrons.py
"""

from benchscale.thirdparty import fetch_all

if __name__ == "__main__":
    print(fetch_all())
