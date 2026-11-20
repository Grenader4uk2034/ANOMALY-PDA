"""Validated reader for the Game Graph payload used by S.T.A.L.K.E.R. Anomaly.

This module parses the Game Graph chunk payload, not an X-Ray .db archive.
All binary layouts use explicit little-endian standard sizes.
"""
from __future__ import annotations

import argparse
import json
import struct
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

HEADER = struct.Struct("<BHII16sB")
VERTEX = struct.Struct("<ffffffBBBBBBBBIIBB")
EDGE = struct.Struct("<Hf")
POINT = struct.Struct("<fffIf")


class GameGraphFormatError(ValueError):
    """Raised when a Game Graph payload is truncated or internally inconsistent."""


@dataclass(frozen=True)
class GraphHeader:
    version: int
    vertex_count: int
    edge_count: int
    level_point_count: int
    guid: str
    level_count: int


@dataclass(frozen=True)
class GraphLevel:
    name: str
    offset: tuple[float, float, float]
    level_id: int
    section: str
    guid: str


@dataclass(frozen=True)
class GraphVertex:
    index: int
    level_point: tuple[float, float, float]
    game_point: tuple[float, float, float]
    level_id: int
    level_vertex_id: int
    vertex_types: tuple[int, int, int, int]
    edge_offset: int
    point_offset: int
    edge_count: int
    point_count: int


@dataclass(frozen=True)
class GraphEdge:
    target_vertex: int
    distance: float


@dataclass(frozen=True)
class GraphPoint:
    position: tuple[float, float, float]
    level_vertex_id: int
    distance: float


class GameGraph:
    """Read and validate a decoded Game Graph chunk."""

    def __init__(self, payload: bytes):
        self.payload = payload
        if len(payload) < HEADER.size:
            raise GameGraphFormatError("payload is shorter than the Game Graph header")
        values = HEADER.unpack_from(payload)
        self.header = GraphHeader(*values[:4], values[4].hex(), values[5])
        self.levels, self.vertex_offset = self._read_levels()
        self.edges_offset = self.vertex_offset + self.header.vertex_count * VERTEX.size
        self.points_offset = self.edges_offset + self.header.edge_count * EDGE.size
        expected_end = self.points_offset + self.header.level_point_count * POINT.size
        if expected_end > len(payload):
            raise GameGraphFormatError(
                f"graph arrays exceed payload: need {expected_end} bytes, have {len(payload)}"
            )
        self.expected_end = expected_end
        self._validate_layout()

    @classmethod
    def from_file(cls, path: str | Path) -> "GameGraph":
        return cls(Path(path).read_bytes())

    def _read_cstring(self, pos: int) -> tuple[str, int]:
        end = self.payload.find(b"\\0", pos)
        if end < 0:
            raise GameGraphFormatError(f"unterminated string at offset {pos}")
        try:
            value = self.payload[pos:end].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise GameGraphFormatError(f"invalid UTF-8 string at offset {pos}") from exc
        return value, end + 1

    def _read_levels(self) -> tuple[tuple[GraphLevel, ...], int]:
        pos = HEADER.size
        levels = []
        for i in range(self.header.level_count):
            name, pos = self._read_cstring(pos)
            if pos + 13 > len(self.payload):
                raise GameGraphFormatError(f"truncated level record {i}")
            x, y, z, level_id = struct.unpack_from("<fffB", self.payload, pos)
            pos += 13
            section, pos = self._read_cstring(pos)
            if pos + 16 > len(self.payload):
                raise GameGraphFormatError(f"truncated level GUID {i}")
            guid = self.payload[pos:pos + 16].hex()
            pos += 16
            levels.append(GraphLevel(name, (x, y, z), level_id, section, guid))
        return tuple(levels), pos

    def iter_vertices(self) -> Iterator[GraphVertex]:
        for index in range(self.header.vertex_count):
            values = VERTEX.unpack_from(self.payload, self.vertex_offset + index * VERTEX.size)
            yield GraphVertex(
                index=index,
                level_point=tuple(values[0:3]),
                game_point=tuple(values[3:6]),
                level_id=values[6],
                level_vertex_id=values[7] | (values[8] << 8) | (values[9] << 16),
                vertex_types=tuple(values[10:14]),
                edge_offset=values[14],
                point_offset=values[15],
                edge_count=values[16],
                point_count=values[17],
            )

    def iter_edges(self) -> Iterator[GraphEdge]:
        for index in range(self.header.edge_count):
            target, distance = EDGE.unpack_from(self.payload, self.edges_offset + index * EDGE.size)
            yield GraphEdge(target, distance)

    def iter_points(self) -> Iterator[GraphPoint]:
        for index in range(self.header.level_point_count):
            x, y, z, level_vertex_id, distance = POINT.unpack_from(
                self.payload, self.points_offset + index * POINT.size
            )
            yield GraphPoint((x, y, z), level_vertex_id, distance)

    def _validate_layout(self) -> None:
        h = self.header
        if h.vertex_count and not self.levels:
            raise GameGraphFormatError("vertices exist but the level table is empty")
        if len({level.level_id for level in self.levels}) != len(self.levels):
            raise GameGraphFormatError("duplicate level IDs in level table")

        edge_total = point_total = 0
        for vertex in self.iter_vertices():
            if vertex.level_id not in {level.level_id for level in self.levels}:
                raise GameGraphFormatError(
                    f"vertex {vertex.index} references unknown level ID {vertex.level_id}"
                )
            if vertex.edge_offset + vertex.edge_count > h.edge_count:
                raise GameGraphFormatError(f"vertex {vertex.index} edge range is out of bounds")
            if vertex.point_offset + vertex.point_count > h.level_point_count:
                raise GameGraphFormatError(f"vertex {vertex.index} point range is out of bounds")
            edge_total += vertex.edge_count
            point_total += vertex.point_count

        if edge_total != h.edge_count:
            raise GameGraphFormatError(
                f"vertex edge counts sum to {edge_total}, header declares {h.edge_count}"
            )
        if point_total != h.level_point_count:
            raise GameGraphFormatError(
                f"vertex point counts sum to {point_total}, header declares {h.level_point_count}"
            )

        for index, edge in enumerate(self.iter_edges()):
            if edge.target_vertex >= h.vertex_count:
                raise GameGraphFormatError(
                    f"edge {index} targets invalid vertex {edge.target_vertex}"
                )

    def summary(self) -> dict:
        return {
            "header": asdict(self.header),
            "levels": len(self.levels),
            "vertex_offset": self.vertex_offset,
            "edges_offset": self.edges_offset,
            "points_offset": self.points_offset,
            "expected_payload_size": self.expected_end,
            "actual_payload_size": len(self.payload),
            "vertices": self.header.vertex_count,
            "edges": self.header.edge_count,
            "level_points": self.header.level_point_count,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a decoded Anomaly Game Graph payload")
    parser.add_argument("payload", type=Path, help="path to the extracted Game Graph chunk")
    args = parser.parse_args()
    graph = GameGraph.from_file(args.payload)
    print(json.dumps(graph.summary(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
