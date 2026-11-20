"""Memory-conscious reader for X-Ray level.ai navigation meshes (versions 10 and 13).

A Level Graph can contain millions of nodes. This parser keeps the original bytes and
decodes vertices on demand instead of allocating millions of Python objects.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

HEADER = struct.Struct("<IIff6fQQ")
VERSION_10 = 10
VERSION_13 = 13
INVALID_LINK_V10 = 0x007FFFFF
INVALID_LINK_V13 = 0x03FFFFFF


class LevelGraphFormatError(ValueError):
    """Raised when level.ai has an unsupported or inconsistent binary layout."""


@dataclass(frozen=True)
class LevelGraphHeader:
    version: int
    vertex_count: int
    cell_size: float
    factor_y: float
    box_min: tuple[float, float, float]
    box_max: tuple[float, float, float]
    guid: str
    row_length: int
    column_length: int


@dataclass(frozen=True)
class LevelVertex:
    index: int
    links: tuple[int | None, int | None, int | None, int | None]
    cover_high: int
    cover_low: int
    plane: int
    xz: int
    y: int


class LevelGraph:
    """Decode Level Graph nodes, their four cardinal links and world positions."""

    def __init__(self, data: bytes):
        self.data = data
        if len(data) < HEADER.size:
            raise LevelGraphFormatError("level.ai is shorter than its 56-byte header")
        raw = HEADER.unpack_from(data)
        version, count, cell_size, factor_y = raw[:4]
        if version not in (VERSION_10, VERSION_13):
            raise LevelGraphFormatError(f"unsupported level.ai version: {version}")
        if not math.isfinite(cell_size) or cell_size <= 0:
            raise LevelGraphFormatError(f"invalid cell_size: {cell_size}")
        if not math.isfinite(factor_y) or factor_y <= 0:
            raise LevelGraphFormatError(f"invalid factor_y: {factor_y}")
        box_min = tuple(raw[4:7])
        box_max = tuple(raw[7:10])
        if not all(math.isfinite(v) for v in (*box_min, *box_max)):
            raise LevelGraphFormatError("non-finite level bounding box")
        if any(box_max[i] < box_min[i] for i in range(3)):
            raise LevelGraphFormatError("invalid level bounding box")

        row_length = max(1, math.floor((box_max[2] - box_min[2]) / cell_size + 0.001 + 1.5))
        column_length = max(1, math.floor((box_max[0] - box_min[0]) / cell_size + 0.001 + 1.5))
        guid = raw[10].to_bytes(8, "little").hex() + raw[11].to_bytes(8, "little").hex()
        self.header = LevelGraphHeader(
            version, count, cell_size, factor_y, box_min, box_max,
            guid, row_length, column_length,
        )
        self.vertex_size = 23 if version == VERSION_10 else 25
        expected = HEADER.size + count * self.vertex_size
        if expected != len(data):
            raise LevelGraphFormatError(
                f"file size mismatch: header/count require {expected} bytes, got {len(data)}"
            )

        # Validate links without retaining decoded vertex objects (large maps have >1M nodes).
        for vertex in self.iter_vertices():
            for target in vertex.links:
                if target is not None and target >= count:
                    raise LevelGraphFormatError(
                        f"vertex {vertex.index} links to out-of-range vertex {target}"
                    )

    @classmethod
    def from_file(cls, path: str | Path) -> "LevelGraph":
        return cls(Path(path).read_bytes())

    @property
    def vertex_count(self) -> int:
        return self.header.vertex_count

    def vertex_at(self, index: int) -> LevelVertex:
        if not 0 <= index < self.vertex_count:
            raise IndexError(f"vertex index {index} outside 0..{self.vertex_count - 1}")
        start = HEADER.size + index * self.vertex_size
        rec = self.data[start:start + self.vertex_size]
        mask_bits = 23 if self.header.version == VERSION_10 else 26
        invalid = INVALID_LINK_V10 if self.header.version == VERSION_10 else INVALID_LINK_V13
        mask = (1 << mask_bits) - 1
        link_bytes = 12 if self.header.version == VERSION_10 else 13
        packed_links = int.from_bytes(rec[:link_bytes], "little")
        links = tuple(
            None if ((packed_links >> (i * mask_bits)) & mask) == invalid
            else ((packed_links >> (i * mask_bits)) & mask)
            for i in range(4)
        )
        pos = link_bytes
        cover_high = int.from_bytes(rec[pos:pos + 2], "little"); pos += 2
        cover_low = int.from_bytes(rec[pos:pos + 2], "little"); pos += 2
        plane = int.from_bytes(rec[pos:pos + 2], "little"); pos += 2
        xz_size = 3 if self.header.version == VERSION_10 else 4
        xz = int.from_bytes(rec[pos:pos + xz_size], "little"); pos += xz_size
        y = int.from_bytes(rec[pos:pos + 2], "little")
        return LevelVertex(index, links, cover_high, cover_low, plane, xz, y)

    def iter_vertices(self) -> Iterator[LevelVertex]:
        for index in range(self.vertex_count):
            yield self.vertex_at(index)

    def vertex_position(self, vertex_id: int) -> tuple[float, float, float]:
        vertex = self.vertex_at(vertex_id)
        gx, gz = divmod(vertex.xz, self.header.row_length)
        x = gx * self.header.cell_size + self.header.box_min[0]
        y = (vertex.y / 65535.0) * self.header.factor_y + self.header.box_min[1]
        z = gz * self.header.cell_size + self.header.box_min[2]
        return x, y, z

    def neighbors(self, vertex_id: int) -> tuple[int | None, ...]:
        return self.vertex_at(vertex_id).links

    def summary(self) -> dict:
        valid_links = sum(
            target is not None
            for vertex in self.iter_vertices()
            for target in vertex.links
        )
        return {
            "header": asdict(self.header),
            "vertex_size": self.vertex_size,
            "file_size": len(self.data),
            "vertices": self.vertex_count,
            "valid_links": valid_links,
            "storage": "lazy; raw binary retained, vertices decoded on demand",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect an Anomaly level.ai navigation graph")
    parser.add_argument("level_ai", type=Path)
    parser.add_argument("--vertex", type=int, help="also print one decoded vertex and its world position")
    args = parser.parse_args()
    graph = LevelGraph.from_file(args.level_ai)
    result = graph.summary()
    if args.vertex is not None:
        if not 0 <= args.vertex < graph.vertex_count:
            parser.error("vertex index is outside the graph")
        result["selected_vertex"] = asdict(graph.vertex_at(args.vertex))
        result["selected_world_position"] = graph.vertex_position(args.vertex)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
