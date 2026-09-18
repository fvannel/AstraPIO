"""Independent geometry audit for a flat DRC witness; never changes a rule."""

from collections import Counter
import math


def flatten_verified(source, target, top_name):
    import gdstk
    import klayout.db as db

    lib = gdstk.read_gds(source)
    top = next(c for c in lib.cells if c.name == top_name)
    top.flatten(apply_repetitions=True)
    if top.references:
        raise ValueError("Flattening left references")
    # Composition of hierarchical label rotations can exceed one revolution.
    # Normalize the angle without moving or changing the label.
    for label in top.labels:
        label.rotation %= math.tau
    flat = gdstk.Library(name="astra_drc_witness", unit=lib.unit, precision=lib.precision)
    flat.add(top)
    flat.write_gds(target)

    # Independent implementation and integer-grid boolean XOR on every layer.
    a, b = db.Layout(), db.Layout()
    a.read(str(source))
    b.read(str(target))
    if a.dbu != b.dbu or len(list(b.each_cell())) != 1:
        raise ValueError("Flattened witness has a different grid or extra cells")
    at, bt = a.cell(top_name), b.cell(top_name)
    am = {(a.get_info(i).layer, a.get_info(i).datatype): i for i in a.layer_indices()}
    bm = {(b.get_info(i).layer, b.get_info(i).datatype): i for i in b.layer_indices()}
    if am.keys() != bm.keys():
        raise ValueError("Layer set changed")

    def labels(cell, layer):
        found = Counter()
        it = cell.begin_shapes_rec(layer)
        while not it.at_end():
            shape = it.shape()
            if shape.is_text():
                text = shape.text.transformed(it.trans())
                found[(text.string, text.trans.disp.x, text.trans.disp.y)] += 1
            it.next()
        return found

    evidence = []
    for key in sorted(am):
        ar = db.Region(at.begin_shapes_rec(am[key]))
        br = db.Region(bt.begin_shapes_rec(bm[key]))
        difference = ar ^ br
        if not difference.is_empty():
            raise ValueError(f"Geometry changed on layer {key}")
        al, bl = labels(at, am[key]), labels(bt, bm[key])
        if al != bl:
            raise ValueError(f"Label locations changed on layer {key}")
        evidence.append({"layer": key, "xor_polygons": 0, "label_count": sum(al.values())})
    return {"scope": "Flat diagnostic copy only; all polygon/path geometry and label locations audited",
            "method": "gdstk flatten, independent KLayout recursive Region XOR at source database grid",
            "database_unit_um": a.dbu, "layers": evidence, "result": "pass"}
