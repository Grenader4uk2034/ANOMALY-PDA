"""Route search over local Level Graphs and the global Game Graph."""
from __future__ import annotations

import heapq
import math
from dataclasses import asdict, dataclass
from typing import Mapping

from .game_graph import GameGraph, GameGraphFormatError
from .level_graph import LevelGraph


class RouteNotFoundError(ValueError):
    """Raised when a route cannot be built from the supplied graph data."""


@dataclass(frozen=True)
class LevelRoute:
    level_id: int
    vertex_ids: tuple[int, ...]


@dataclass(frozen=True)
class LevelTransition:
    from_level_id: int
    from_level_vertex: int
    to_level_id: int
    to_level_vertex: int
    game_edge_distance: float


def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.dist(a, b)


def find_level_path(graph: LevelGraph, start: int, goal: int) -> tuple[int, ...] | None:
    """A* over the four packed cardinal links in one level.ai."""
    if not (0 <= start < graph.vertex_count and 0 <= goal < graph.vertex_count):
        return None
    if start == goal:
        return (start,)

    goal_pos = graph.vertex_position(goal)
    open_heap: list[tuple[float, float, int]] = [
        (_distance(graph.vertex_position(start), goal_pos), 0.0, start)
    ]
    g_score = {start: 0.0}
    came_from: dict[int, int] = {}

    while open_heap:
        _f, current_g, current = heapq.heappop(open_heap)
        if current_g != g_score.get(current):
            continue
        if current == goal:
            path = [goal]
            while path[-1] != start:
                path.append(came_from[path[-1]])
            path.reverse()
            return tuple(path)

        current_pos = graph.vertex_position(current)
        for neighbor in graph.neighbors(current):
            if neighbor is None:
                continue
            next_pos = graph.vertex_position(neighbor)
            candidate = current_g + _distance(current_pos, next_pos)
            if candidate < g_score.get(neighbor, math.inf):
                g_score[neighbor] = candidate
                came_from[neighbor] = current
                estimate = candidate + _distance(next_pos, goal_pos)
                heapq.heappush(open_heap, (estimate, candidate, neighbor))
    return None


def find_game_path(game_graph: GameGraph, start: int, goal: int) -> tuple[int, ...] | None:
    """Dijkstra over inter-level Game Graph edges (uses engine edge.distance)."""
    count = len(game_graph.vertices)
    if not (0 <= start < count and 0 <= goal < count):
        return None
    if start == goal:
        return (start,)

    open_heap: list[tuple[float, int]] = [(0.0, start)]
    distances = {start: 0.0}
    came_from: dict[int, int] = {}

    while open_heap:
        current_cost, current = heapq.heappop(open_heap)
        if current_cost != distances.get(current):
            continue
        if current == goal:
            path = [goal]
            while path[-1] != start:
                path.append(came_from[path[-1]])
            path.reverse()
            return tuple(path)

        for edge in game_graph.vertex_edges(current):
            neighbor = edge.target_vertex
            candidate = current_cost + max(0.0, edge.distance)
            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                came_from[neighbor] = current
                heapq.heappush(open_heap, (candidate, neighbor))
    return None


def build_route(
    game_graph: GameGraph,
    level_graphs: Mapping[int, LevelGraph],
    start_level_id: int,
    start_level_vertex: int,
    goal_level_id: int,
    goal_level_vertex: int,
) -> dict:
    """Build local walking segments joined by Game Graph level transitions.

    All Level Graphs encountered on the global path must be supplied and must match
    their embedded Cross Tables by vertex count and GUID.
    """
    if start_level_id not in level_graphs or goal_level_id not in level_graphs:
        raise RouteNotFoundError("start or destination Level Graph was not supplied")

    try:
        game_graph.validate_level_graph(start_level_id, level_graphs[start_level_id])
        game_graph.validate_level_graph(goal_level_id, level_graphs[goal_level_id])
    except GameGraphFormatError as exc:
        raise RouteNotFoundError(str(exc)) from exc

    start_cell = game_graph.resolve_game_vertex(start_level_id, start_level_vertex)
    goal_cell = game_graph.resolve_game_vertex(goal_level_id, goal_level_vertex)
    if start_cell is None or goal_cell is None:
        raise RouteNotFoundError("Cross Table does not contain the start or destination vertex")

    global_path = find_game_path(game_graph, start_cell.game_vertex_id, goal_cell.game_vertex_id)
    if global_path is None:
        raise RouteNotFoundError("no inter-level route exists in the Game Graph")

    path_levels = {game_graph.vertices[index].level_id for index in global_path}
    for level_id in path_levels:
        level_graph = level_graphs.get(level_id)
        if level_graph is None:
            raise RouteNotFoundError(f"Level Graph for intermediate level {level_id} was not supplied")
        try:
            game_graph.validate_level_graph(level_id, level_graph)
        except GameGraphFormatError as exc:
            raise RouteNotFoundError(str(exc)) from exc

    first_game_vertex = game_graph.vertices[global_path[0]]
    first_level_path = find_level_path(
        level_graphs[start_level_id],
        start_level_vertex,
        first_game_vertex.level_vertex_id,
    )
    if first_level_path is None:
        raise RouteNotFoundError("start point cannot reach its mapped Game Graph vertex")

    segments: list[LevelRoute] = []
    transitions: list[LevelTransition] = []
    current_level = start_level_id
    current_segment = list(first_level_path)

    for left_id, right_id in zip(global_path, global_path[1:]):
        left = game_graph.vertices[left_id]
        right = game_graph.vertices[right_id]
        if left.level_id == right.level_id:
            local_path = find_level_path(
                level_graphs[left.level_id],
                left.level_vertex_id,
                right.level_vertex_id,
            )
            if local_path is None:
                raise RouteNotFoundError(
                    f"no local path between vertices {left.level_vertex_id} and {right.level_vertex_id} "
                    f"on level {left.level_id}"
                )
            current_segment.extend(local_path[1:])
        else:
            if current_segment:
                segments.append(LevelRoute(current_level, tuple(current_segment)))
            crossing = next(
                (edge for edge in game_graph.vertex_edges(left_id) if edge.target_vertex == right_id),
                None,
            )
            transitions.append(LevelTransition(
                left.level_id, left.level_vertex_id,
                right.level_id, right.level_vertex_id,
                crossing.distance if crossing else 0.0,
            ))
            current_level = right.level_id
            current_segment = [right.level_vertex_id]

    last_game_vertex = game_graph.vertices[global_path[-1]]
    final_path = find_level_path(
        level_graphs[goal_level_id],
        last_game_vertex.level_vertex_id,
        goal_level_vertex,
    )
    if final_path is None:
        raise RouteNotFoundError("mapped Game Graph vertex cannot reach the destination locally")
    current_segment.extend(final_path[1:])
    if current_segment:
        segments.append(LevelRoute(current_level, tuple(current_segment)))

    return {
        "start": {"level_id": start_level_id, "level_vertex": start_level_vertex},
        "goal": {"level_id": goal_level_id, "level_vertex": goal_level_vertex},
        "global_game_path": list(global_path),
        "segments": [asdict(segment) for segment in segments],
        "transitions": [asdict(item) for item in transitions],
    }
