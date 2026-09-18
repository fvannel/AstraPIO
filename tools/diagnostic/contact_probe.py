"""Non-production, byte-local contact recentering experiment for IHP #794.

This does NOT edit a PDK, rule deck, source layout, or release configuration.
The commercial-rule evidence in IHP #819 means this experiment is not a
recommendation to alter the characterized provider macro for fabrication.
"""

import struct


DELAY = "RSC_IHPSG13_CDLYX1"
CORNER = "RM_IHPSG13_1P_BITKIT_CELL_CORNER"
TARGETS = {
    DELAY: [((175, 570, 335, 730), (0, -10)),
            ((1195, 570, 1355, 730), (0, -10)),
            ((2215, 570, 2375, 730), (0, -10))],
    CORNER: [((115, -80, 275, 80), (10, 0))],
}


def recenter(data, variant, prefix="", repair_corner_metal=False):
    """Change only exact known XY records in a verified 1 nm-unit GDS.

    Caller must verify the input hash and units. Reject missing/duplicate
    geometry and malformed records. The returned manifest identifies every
    changed byte range; all bytes outside those XY payloads are untouched.
    """
    if variant not in ("delay", "corner", "both"):
        raise ValueError("Unknown contact experiment")
    if repair_corner_metal and variant == "delay":
        raise ValueError("Metal repair requires the corner contact experiment")
    wanted = {prefix + name: shapes for name, shapes in TARGETS.items()
              if variant == "both" or name == (DELAY if variant == "delay" else CORNER)}
    output = bytearray(data)
    offset, cell, element, layer, datatype = 0, None, None, None, None
    changed, matched = [], set()
    while offset < len(data):
        if offset + 4 > len(data):
            raise ValueError("Truncated GDS record")
        size, record, value_type = struct.unpack_from(">HBB", data, offset)
        if size < 4 or size % 2 or offset + size > len(data):
            raise ValueError("Invalid GDS record length")
        payload = data[offset + 4:offset + size]
        if record == 0x04:  # ENDLIB; some provider streams pad with zero bytes.
            if any(data[offset + size:]):
                raise ValueError("Unexpected nonzero bytes after ENDLIB")
            break
        if record == 0x06:  # STRNAME
            cell = payload.rstrip(b"\0").decode("ascii")
        elif record == 0x07:  # ENDSTR
            cell = None
        elif record in (0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x15, 0x2D):
            element, layer, datatype = record, None, None
        elif record == 0x0D:
            layer = struct.unpack(">h", payload)[0]
        elif record == 0x0E:
            datatype = struct.unpack(">h", payload)[0]
        elif record == 0x10 and cell in wanted and element == 0x08 and (
                (layer, datatype) == (6, 0) or
                (repair_corner_metal and cell == prefix + CORNER and (layer, datatype) == (8, 0))):
            if value_type != 3 or len(payload) % 8:
                raise ValueError("Unexpected XY encoding")
            values = struct.unpack(">" + "i" * (len(payload) // 4), payload)
            points = list(zip(values[::2], values[1::2]))
            bbox = (min(values[::2]), min(values[1::2]),
                    max(values[::2]), max(values[1::2]))
            candidates = wanted[cell] if layer == 6 else [((-145, -105, 325, 105), (10, 0))]
            for expected, (dx, dy) in candidates:
                if bbox != expected:
                    continue
                rectangle = {(bbox[0], bbox[1]), (bbox[2], bbox[1]),
                             (bbox[2], bbox[3]), (bbox[0], bbox[3])}
                if len(points) != 5 or points[0] != points[-1] or set(points) != rectangle:
                    raise ValueError("Target is not an exact rectangular contact")
                key = (cell, layer, bbox)
                if key in matched:
                    raise ValueError("Duplicate target contact")
                matched.add(key)
                after = ([(x + dx, y + dy) for x, y in points] if layer == 6 else
                         [(x + 10 if x == 325 else x, y) for x, y in points])
                encoded = struct.pack(">" + "i" * len(values), *(v for p in after for v in p))
                output[offset + 4:offset + size] = encoded
                changed.append({"cell": cell, "layer": [layer, 0], "bbox_before_nm": bbox,
                                "operation": "translation" if layer == 6 else "extend_right_edge",
                                "delta_nm": [dx, dy], "offset": offset + 4,
                                "length": len(payload), "before_hex": payload.hex(),
                                "after_hex": encoded.hex()})
        elif record == 0x11:
            element = None
        offset += size
    if len(matched) != sum(len(shapes) for shapes in wanted.values()) + int(repair_corner_metal):
        raise ValueError("Not all exact contact targets were found")
    restored = bytearray(output)
    for entry in changed:
        start = entry["offset"]
        restored[start:start + entry["length"]] = bytes.fromhex(entry["before_hex"])
    if bytes(restored) != data or len(output) != len(data):
        raise ValueError("Bytes outside allowed XY payloads changed")
    return bytes(output), changed
