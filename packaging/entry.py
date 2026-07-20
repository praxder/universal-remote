"""PyInstaller entry point for the frozen binary.

Kept separate from ``universal_remote.cli`` because PyInstaller needs a real
script file as its build target; the module itself is bundled via
``--collect-submodules universal_remote``.
"""

from universal_remote.cli import main

if __name__ == "__main__":
    main()
