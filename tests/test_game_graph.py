import struct
import unittest

from anomaly_pda.game_graph import (
    GameGraph, GameGraphFormatError, HEADER, VERTEX, EDGE, CROSS_HEADER,
)
from anomaly_pda.level_graph import LevelGraph, LevelGraphFormatError, HEADER as AI_HEADER
from anomaly_pda.routing import find_level_path, build_route


def make_payload():
    # One level, one vertex, no edges, no points, no embedded cross tables.
    guid = bytes(range(16))
    level = b"test_level\0" + struct.pack("<fffB", 1.0, 2.0, 3.0, 0)
    level += b"level01\0" + guid
    header = HEADER.pack(10, 1, 0, 0, guid, 1)
    vertex = VERTEX.pack(
        1.0, 2.0, 3.0, 4.0, 5.0, 6.0,
        0, 7, 0, 0, 1, 2, 3, 4,
        0, 0, 0, 0,
    )
    return header + level + vertex


def make_level_ai(version=10, guid_bytes=None):
    # Two nodes linked 0 <-> 1, with a flat test world.
    count = 2
    guid_bytes = guid_bytes if guid_bytes is not None else bytes(range(16))
    guid_a = int.from_bytes(guid_bytes[:8], "little")
    guid_b = int.from_bytes(guid_bytes[8:], "little")
    buf = bytearray(AI_HEADER.pack(
        version, count, 1.0, 10.0,
        -2.0, 0.0, -2.0, 4.0, 10.0, 4.0,
        guid_a, guid_b,
    ))
    bits = 23 if version == 10 else 26
    invalid = (1 << bits) - 1
    for links, xz, y in [([1, invalid, invalid, invalid], 0, 0),
                         ([0, invalid, invalid, invalid], 1, 32767)]:
        packed = sum((link & invalid) << (i * bits) for i, link in enumerate(links))
        buf.extend(packed.to_bytes(12 if version == 10 else 13, "little"))
        buf.extend((0x1234).to_bytes(2, "little"))
        buf.extend((0xABCD).to_bytes(2, "little"))
        buf.extend((0x2000).to_bytes(2, "little"))
        buf.extend(xz.to_bytes(3 if version == 10 else 4, "little"))
        buf.extend(y.to_bytes(2, "little"))
    return bytes(buf)


class GameGraphTests(unittest.TestCase):
    def test_reads_header_level_and_vertex(self):
        graph = GameGraph(make_payload())
        self.assertEqual(graph.header.version, 10)
        self.assertEqual(graph.header.vertex_count, 1)
        self.assertEqual(graph.levels[0].section, "level01")
        vertex = graph.vertices[0]
        self.assertEqual(vertex.level_vertex_id, 7)
        self.assertEqual(vertex.game_point, (4.0, 5.0, 6.0))

    def test_rejects_truncated_payload(self):
        with self.assertRaises(GameGraphFormatError):
            GameGraph(make_payload()[:-1])

    def test_reads_embedded_cross_table_and_builds_route(self):
        level_guid = bytes(range(16))
        level = b"test\0" + struct.pack("<fffB", 0.0, 0.0, 0.0, 0)
        level += b"level01\0" + level_guid
        header = HEADER.pack(10, 1, 1, 0, level_guid, 1)
        # Offsets are byte offsets relative to the start of the vertex array.
        vertex = VERTEX.pack(0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 42, 48, 1, 0)
        edge = EDGE.pack(0, 1.25)
        guid_a = int.from_bytes(level_guid[:8], "little")
        guid_b = int.from_bytes(level_guid[8:], "little")
        ct_header = CROSS_HEADER.pack(9, 2, 1, guid_a, guid_b, guid_a, guid_b)
        cells = EDGE.pack(0, 0.5) + EDGE.pack(0, 1.0)
        ct_payload = ct_header + cells
        ct_block = struct.pack("<I", 4 + len(ct_payload)) + ct_payload
        graph = GameGraph(header + level + vertex + edge + ct_block)

        self.assertEqual(graph.edges[0].target_vertex, 0)
        self.assertEqual(len(graph.cross_tables), 1)
        self.assertEqual(graph.resolve_game_vertex(0, 1).distance, 1.0)

        local_graph = LevelGraph(make_level_ai(guid_bytes=level_guid))
        self.assertTrue(graph.validate_level_graph(0, local_graph)["level_guid_match"])
        route = build_route(graph, {0: local_graph}, 0, 0, 0, 1)
        self.assertEqual(route["segments"][0]["vertex_ids"], (0, 1))

    def test_rejects_invalid_edge_target(self):
        guid = bytes(16)
        level = b"test\0" + struct.pack("<fffB", 0.0, 0.0, 0.0, 0)
        level += b"level01\0" + guid
        header = HEADER.pack(10, 1, 1, 0, guid, 1)
        vertex = VERTEX.pack(0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 42, 48, 1, 0)
        with self.assertRaises(GameGraphFormatError):
            GameGraph(header + level + vertex + EDGE.pack(1, 1.0))


class LevelGraphTests(unittest.TestCase):
    def test_parses_v10_and_decodes_links_and_positions(self):
        graph = LevelGraph(make_level_ai(10))
        self.assertEqual(graph.header.vertex_count, 2)
        self.assertEqual(graph.vertex_at(0).links[0], 1)
        self.assertIsNone(graph.vertex_at(0).links[1])
        self.assertAlmostEqual(graph.vertex_position(0)[0], -2.0)
        self.assertAlmostEqual(graph.vertex_position(1)[2], -1.0)

    def test_parses_v13(self):
        graph = LevelGraph(make_level_ai(13))
        self.assertEqual(graph.header.version, 13)
        self.assertEqual(graph.vertex_at(1).links[0], 0)

    def test_rejects_truncated_level_ai(self):
        with self.assertRaises(LevelGraphFormatError):
            LevelGraph(make_level_ai()[:-1])

    def test_local_astar_route(self):
        graph = LevelGraph(make_level_ai())
        self.assertEqual(find_level_path(graph, 0, 1), (0, 1))
        self.assertEqual(find_level_path(graph, 1, 0), (1, 0))


if __name__ == "__main__":
    unittest.main()
