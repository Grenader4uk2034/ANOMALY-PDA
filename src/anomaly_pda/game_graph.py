"""Reader for Anomaly's Game Graph payload, including embedded per-level Cross Tables.

Input is the decoded type-4 Game Graph chunk payload from all.spawn/spawns.db0,
not the outer X-Ray DB archive or the outer all.spawn chunk envelope.
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
CROSS_HEADER = struct.Struct("<IIIQQQQ")


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


@dataclass(frozen=True)
class CrossTableHeader:
    version: int
    level_vertex_count: int
    game_vertex_count: int
    level_guid: str
    game_guid: str


@dataclass(frozen=True)
class CrossTableCell:
    game_vertex_id: int
    distance: float


@dataclass(frozen=True)
class LevelCrossTable:
    level_id: int
    header: CrossTableHeader
    cell_data: memoryview
    cell_count: int

    def cell_at(self, level_vertex_id: int) -> CrossTableCell | None:
        if not 0 <= level_vertex_id < self.cell_count:
            return None
        return CrossTableCell(*EDGE.unpack_from(self.cell_data, level_vertex_id * EDGE.size))


class GameGraph:
    """Read and validate a decoded Game Graph chunk, including its embedded GCT blocks."""

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
        self.vertices = tuple(self.iter_vertices())
        self.edges = tuple(self.iter_edges())
        self.cross_tables = self._read_embedded_cross_tables(expected_end)
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

    def _read_embedded_cross_tables(self, pos: int) -> tuple[LevelCrossTable, ...]:
        tables = []
        # Engine serializes embedded cross-table blocks in ascending level ID order.
        for level in sorted(self.levels, key=lambda item: item.level_id):
            if pos == len(self.payload):
                break
            if pos + 4 > len(self.payload):
                raise GameGraphFormatError("truncated embedded Cross Table block-size field")
            block_size = struct.unpack_from("<I", self.payload, pos)[0]
            if block_size < 4 + CROSS_HEADER.size:
                raise GameGraphFormatError(
                    f"invalid Cross Table block size {block_size} for level {level.level_id}"
                )
            block_end = pos + block_size
            if block_end > len(self.payload):
                raise GameGraphFormatError(
                    f"Cross Table for level {level.level_id} exceeds Game Graph payload"
                )
            raw_start = pos + 4
            version, level_count, game_count, *guids = CROSS_HEADER.unpack_from(self.payload, raw_start)
            raw_size = block_size - 4
            expected = CROSS_HEADER.size + level_count * EDGE.size
            if expected != raw_size:
                raise GameGraphFormatError(
                    f"Cross Table level {level.level_id}: expected {expected} bytes, got {raw_size}"
                )
            cell_start = raw_start + CROSS_HEADER.size
            cell_data = memoryview(self.payload)[cell_start:block_end]
            for i in range(level_count):
                game_vertex_id, _distance = EDGE.unpack_from(cell_data, i * EDGE.size)
                if game_vertex_id >= self.header.vertex_count:
                    raise GameGraphFormatError(
                        f"Cross Table for level {level.level_id} references invalid Game Graph vertex"
                    )
            tables.append(LevelCrossTable(
                level.level_id,
                CrossTableHeader(
                    version, level_count, game_count,
                    guids[0].to_bytes(8, "little").hex() + guids[1].to_bytes(8, "little").hex(),
                    guids[2].to_bytes(8, "little").hex() + guids[3].to_bytes(8, "little").hex(),
                ),
                cell_data,
                level_count,
            ))
            pos = block_end

        if pos != len(self.payload):
            raise GameGraphFormatError(
                f"{len(self.payload) - pos} unexpected trailing bytes after embedded Cross Tables"
            )
        return tuple(tables)

    def cross_table_for_level(self, level_id: int) -> LevelCrossTable | None:
        return next((table for table in self.cross_tables if table.level_id == level_id), None)

    def resolve_game_vertex(self, level_id: int, level_vertex_id: int) -> CrossTableCell | None:
        table = self.cross_table_for_level(level_id)
        if table is None:
            return None
        return table.cell_at(level_vertex_id)

    def _validate_layout(self) -> None:
        h = self.header
        level_ids = {level.level_id for level in self.levels}
        if h.vertex_count and not self.levels:
            raise GameGraphFormatError("vertices exist but the level table is empty")
        if len(level_ids) != len(self.levels):
            raise GameGraphFormatError("duplicate level IDs in level table")

        edge_total = point_total = 0
        edge_base_rel = h.vertex_count * VERTEX.size
        point_base_rel = edge_base_rel + h.edge_count * EDGE.size
        for vertex in self.vertices:
            if vertex.level_id not in level_ids:
                raise GameGraphFormatError(
                    f"vertex {vertex.index} references unknown level ID {vertex.level_id}"
                )
            # X-Ray stores these as byte offsets relative to the beginning of the vertex array,
            # not as edge/point indices.
            if vertex.edge_count:
                delta = vertex.edge_offset - edge_base_rel
                if delta < 0 or delta % EDGE.size or delta // EDGE.size + vertex.edge_count > h.edge_count:
                    raise GameGraphFormatError(f"vertex {vertex.index} edge byte range is invalid")
            if vertex.point_count:
                delta = vertex.point_offset - point_base_rel
                if delta < 0 or delta % POINT.size or delta // POINT.size + vertex.point_count > h.level_point_count:
                    raise GameGraphFormatError(f"vertex {vertex.index} point byte range is invalid")
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

        for index, edge in enumerate(self.edges):
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
            "arrays_end_offset": self.expected_end,
            "actual_payload_size": len(self.payload),
            "vertices": len(self.vertices),
            "edges": len(self.edges),
            "level_points": self.header.level_point_count,
            "embedded_cross_tables": len(self.cross_tables),
            "cross_table_cells": sum(table.cell_count for table in self.cross_tables),
            "point_storage": "lazy iterator; no per-point Python objects retained",
            "cross_table_storage": "memoryview; cells decoded on demand",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a decoded Anomaly Game Graph payload")
    parser.add_argument("payload", type=Path, help="path to the extracted Game Graph chunk")
    args = parser.parse_args()
    graph = GameGraph.from_file(args.payload)
    print(json.dumps(graph.summary(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
