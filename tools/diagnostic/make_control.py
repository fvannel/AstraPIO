"""Generate a small metal-only diagnostic witness, not a submitted circuit."""

import datetime
from pathlib import Path
import sys

import gdstk


def write_control(target, negative=False):
    library = gdstk.Library(unit=1e-6, precision=1e-9)
    cell = library.new_cell("astra_metal_control")
    # IHP Metal1.drawing is 8/0; 2 um square exercises non-empty geometry.
    # Negative witness deliberately violates the minimum Metal1 width.
    cell.add(gdstk.rectangle((0, 0), (2, 0.1 if negative else 2), layer=8, datatype=0))
    library.write_gds(target, timestamp=datetime.datetime(2026, 9, 18))


if __name__ == "__main__":
    write_control(Path(sys.argv[1]))
