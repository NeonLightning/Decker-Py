# Decker Python

A Linux desktop port of Shawn Overcash's 2001 Windows MFC cyberspace RPG. The Python edition uses the repository's original BMP and WAV assets and preserves the home, deck, contract, shop, project, rest, and matrix gameplay loops.

## Requirements

- Python 3.10 or newer
- Pygame 2.6 or newer

The package includes copies of the required files from the original `DefaultGraphics`, `Sound`, and `RES` directories; no separate asset download is required.

## Run from source

From the repository root:

```sh
python3 -m pip install --user ./decker_py
./decker_py/run.sh
```

Or run without installing the package:

```sh
cd decker_py
python3 -m decker
```

If installation reports an externally managed Python environment, use a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/pip install -e decker_py
.venv/bin/decker
```

## Controls

- Mouse: use the original bitmap buttons and dialog controls.
- `W`, `A`, `S`, `D`: move through matrix nodes.
- `Ctrl+S` or `F5`: quick save.
- `Ctrl+L` or `F9`: load the latest save.
- `Esc`: close a dialog, disconnect from a run, or return to the title screen.

Python saves are JSON files under `~/.local/share/decker/`. They are deliberately portable and human-readable. Legacy MFC `.DSG` binary saves are not loaded by this port.

## Gameplay

Create a character, accept a contract, buy and load programs, then enter the Matrix. Explore the generated system map, defeat or deceive ICE, operate datastore/CPU/I/O nodes, and complete the target objective before disconnecting. Successful runs pay credits and raise reputation. Rest advances project, shop-order, and contract clocks.

## Development

```sh
python3 -m compileall -q decker
python3 -m pytest
```

## License

The original game source and bundled materials were released under GNU GPL version 2 or later. This Python port remains licensed under GPL-2.0-or-later. See `LICENSE` and the original source headers for attribution.
