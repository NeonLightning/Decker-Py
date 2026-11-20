# Decker Py

The original 2001 Windows MFC/C++ source for **Decker: A Cyberspace RPG**, together with an actively developed Linux Python/Pygame port.

The Python edition is in [`decker_py/`](decker_py/). It includes the original bitmap and sound assets and recreates the home screen, contracts, shop, projects, cyberdeck, and Matrix gameplay.

## Run the Python port

```sh
python3 -m pip install --user ./decker_py
decker
```

Or run it directly from the checkout:

```sh
./decker_py/run.sh
```

See [`decker_py/README.md`](decker_py/README.md) for controls, save locations, development instructions, and current compatibility details.

## Original game

The Visual C++ 6/MFC project remains at the repository root. Historical installation artifacts are in [`bin/`](bin/), bundled graphics in [`DefaultGraphics/`](DefaultGraphics/), sounds in [`Sound/`](Sound/), and Windows program resources in [`RES/`](RES/).

The original game was created by Shawn Overcash and released under GNU GPL version 2 or later. The Python port preserves that license and includes the original license text in [`decker_py/LICENSE`](decker_py/LICENSE).

## License

GPL-2.0-or-later. See the source headers and [`decker_py/LICENSE`](decker_py/LICENSE).
