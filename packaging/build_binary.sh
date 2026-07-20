#!/usr/bin/env bash
# Build the standalone macOS arm64 binary for universal-remote.
#
# Produces a self-contained application directory at dist/universal-remote/ (an
# --onedir bundle: the launcher at dist/universal-remote/universal-remote plus an
# _internal/ directory of dependencies) that runs with no user-provided Python or
# uv. Unlike --onefile, it runs in place with no per-launch temp extraction. The
# flags below bundle Textual's framework
# CSS and the dynamic-import runtime dependencies that PyInstaller's static
# analysis cannot discover on its own:
#   --collect-all textual            Textual ships CSS/data files, not just code.
#   --collect-submodules ...         Bundle every adapter module in the package.
#   --collect-all <dep>              zeroconf/pyatv/androidtvremote2/adb_shell/
#                                    protobuf import submodules dynamically.
#   --recursive-copy-metadata ...    Several deps (e.g. rokuecp) and the CLI call
#                                    importlib.metadata.version() at import time,
#                                    which needs the packaged dist-info metadata.
set -euo pipefail

cd "$(dirname "$0")/.."

uv run pyinstaller \
  --onedir \
  --name universal-remote \
  --collect-all textual \
  --collect-submodules universal_remote \
  --collect-all zeroconf \
  --collect-all pyatv \
  --collect-all androidtvremote2 \
  --collect-all adb_shell \
  --collect-all google.protobuf \
  --recursive-copy-metadata universal-remote \
  --noconfirm \
  packaging/entry.py

echo "Built dist/universal-remote/ (launcher: dist/universal-remote/universal-remote)"
