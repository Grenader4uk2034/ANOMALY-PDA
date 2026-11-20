import struct
import unittest

from anomaly_pda.game_graph import GameGraph, GameGraphFormatError, HEADER, VERTEX, EDGE, POINT


def make_payload():
    # One level, one vertex, no edges, no level points.
    level = b"test_level\\0" + struct.pack("<fffB", 1.0, 2.0, 3.0, 0)
    level += b"level01\\0" + bytes(range(16))
    header = HEADER.pack(10, 1, 0, 0, bytes(range(16)), 1)
    vertex = VERTEX.pack(
        1.0, 2.0, 3.0, 4.0, 5.0, 6.0,
        0, 7, 0, 0, 1, 2, 3, 4,
        0, 0, 0, 0,
    )
    return header + level + vertex


class GameGraphTests(unittest.TestCase):
    def test_reads_header_level_and_vertex(self):
        graph = GameGraph(make_payload())
        self.assertEqual(graph.header.version, 10)
        self.assertEqual(graph.header.vertex_count, 1)
        self.assertEqual(graph.levels[0].section, "level01")
        vertex = next(graph.iter_vertices())
        self.assertEqual(vertex.level_vertex_id, 7)
        self.assertEqual(vertex.game_point, (4.0, 5.0, 6.0))

    def test_rejects_truncated_payload(self):
        with self.assertRaises(GameGraphFormatError):
            GameGraph(make_payload()[:-1])

    def test_reads_edge_and_point_records(self):
        level = b"test\\0" + struct.pack("<fffB", 0.0, 0.0, 0.0, 0)
        level += b"level01\\0" + bytes(16)
        header = HEADER.pack(10, 1, 1, 1, bytes(16), 1)
        vertex = VERTEX.pack(0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1)
        edge = EDGE.pack(0, 1.25)
        point = POINT.pack(1.0, 2.0, 3.0, 9, 2.5)
        graph = GameGraph(header + level + vertex + edge + point)
        self.assertEqual(next(graph.iter_edges()).target_vertex, 0)
        self.assertEqual(next(graph.iter_points()).level_vertex_id, 9)


if __name__ == "__main__":
    unittest.main()
