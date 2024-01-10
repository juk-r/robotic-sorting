import collections
import dataclasses
import itertools
import typing

from brains.brain import Brain
from robot import Robot
from structures import Map, Position, Direction, RobotType
from brains.algorithms import LinkedList, TrueItem, Item, PathSpan, a_star, dijkstra, restore_path
from modelling import Model
from cell import Cell
from maps import OneWayMap

VertexT = typing.TypeVar("VertexT")
State = tuple[Position, Direction]
INF = float('inf')

@dataclasses.dataclass(frozen=True, slots=True)
class TimedVertex(typing.Generic[VertexT]):
    vertex: VertexT
    interval: Item["Reservation"]

    @typing.override
    def __repr__(self):
        return str(self.vertex)


@dataclasses.dataclass(frozen=True, slots=True)
class Reservation:
    reserve_from: float
    be_from: float
    be_until: float
    reserve_until: float
    @typing.override
    def __repr__(self):
        return f"({self.reserve_from}-{self.reserve_until})"


class PathBrain(Brain[Map[Cell], Robot[Cell]]):
    def __init__(self, 
                 model: Model[Map[Cell], typing.Self, Robot[Cell]],
                 robot_type: RobotType,
                 rebuild_path: bool = False,
                 personal_rest: bool = True) -> None:
        super().__init__(model)
        self.robot_type = robot_type
        self._reserves: dict[Position, LinkedList[Reservation]] = {
            v: LinkedList() for v in model.map}
        self._robots_paths: dict[
            Robot[Cell], 
            collections.deque[PathSpan[TimedVertex[State]]]] = {}
        self._robots_reserves: dict[
            Robot[Cell], 
            collections.deque[TrueItem[Reservation]]] = {}
        self._destinations: dict[Robot[Cell], int] = {}
        self._last = -1
        self._current: dict[Robot[Cell], TrueItem[Reservation]] = {}
        self._prev: dict[Robot[Cell], TrueItem[Reservation]] = {}
        self._generate_to_input: dict[Robot[Cell], bool] = {}
        self._generate_to_output: dict[Robot[Cell], bool] = {}
        self._count_ends: list[int] = []
        self._avoid_puts: float = 0 # NOT WORKING
        self.path_adder: typing.Callable[
            [Robot[Cell],float,float,Position,Position],
            tuple[list[PathSpan[TimedVertex[State]]], list[TrueItem[Reservation]]]] = \
            self._add_path_for_position
        self._rebuild_path: bool = rebuild_path
        self.robots_rests: dict[Robot[Cell], Position] = {}
        self.rests: list[Position] = []
        self.personal_rest = personal_rest

    @typing.override
    def new_robot(self, robot: Robot[Cell]):
        self._robots_paths[robot] = collections.deque()
        self._robots_reserves[robot] = collections.deque()
        self._current[robot] = self._reserves[robot.position].add_before(
            Reservation(self._model.now, self._model.now, INF, INF))
        self._generate_to_input[robot] = True
        self._generate_to_output[robot] = False

    @typing.override
    def get_next_action(self, robot: Robot[Cell]) -> Robot.Action:
        if self._generate_to_input[robot]:
            self._generate_to_input[robot] = False
            self._assign_input(robot)
            self._clear_path(robot)
            self._generate_input_path(robot)
        if self._generate_to_output[robot]:
            self._generate_to_output[robot] = False
            self._clear_path(robot)
            self._generate_output_path(robot)
        new_state = self._robots_paths[robot][0]
        if (robot.mail is not None
                and robot.position == self._model.map.outputs[robot.mail.destination]
                and new_state.start - self._model.now >= self.robot_type.time_to_put):
            self._generate_to_input[robot] = True
            self._count += 1
            self._current[robot].remove()
            self._current[robot] = self._robots_reserves[robot].popleft()
            return Robot.Action.put
        if (robot.mail is None
                and robot.position == self._model.map.inputs[self._destinations[robot]]
                and new_state.start - self._model.now >= self.robot_type.time_to_take):
            self._generate_to_output[robot] = True
            self._current[robot].remove()
            self._current[robot] = self._robots_reserves[robot].popleft()
            return Robot.Action.take
        if self._current[robot].val.reserve_until <= self._model.now:
            self._current[robot].remove()
            self._current[robot] = self._robots_reserves[robot].popleft()
        if (new_state.start != self._model.now and
                self._rebuild_path and 
                self._robots_reserves[robot][0].prev == self._reserves[new_state.vertex_to.vertex[0]]):
            self._clear_path(robot)
            if robot.mail is None:
                self._generate_input_path(robot)
            else:
                self._generate_output_path(robot)
            new_state = self._robots_paths[robot][0]
        if new_state.start != self._model.now:
            self._model.process(self._abort(new_state.start - self._model.now, robot))
            return Robot.Action.idle
        self._robots_paths[robot].popleft()
        if new_state.vertex_to.vertex[0] == robot.position and new_state.vertex_to.vertex[1] != robot.direction:
            return Robot.Action.turn_to(new_state.vertex_to.vertex[1])
        if new_state.vertex_to.vertex[1] == robot.direction and new_state.vertex_to.vertex[0] != robot.position:
            return Robot.Action.move
        raise Exception("Wrong path.")

    def _clear_path(self, robot: Robot[Cell]):
        for path_span in self._robots_reserves[robot]:
            path_span.remove()
        self._robots_reserves[robot].clear()
        self._robots_paths[robot].clear()

    def _generate_input_path(self, robot: Robot[Cell]):
        if self.personal_rest:
            res = self.path_adder(
            robot,
            self._model.now,
            self.robot_type.time_to_take,
            self._model.map.inputs[self._destinations[robot]],
            self.robots_rests[robot]
        )
        else:
            res = self._add_path_for_closest_rest(
                robot,
                self._model.now,
                self.robot_type.time_to_take,
                self._model.map.inputs[self._destinations[robot]],
            )
        self._robots_paths[robot].extend(res[0])
        self._robots_reserves[robot].extend(res[1])
        self._current[robot] = self._robots_reserves[robot].popleft()

    def _assign_input(self, robot: Robot[Cell]):
        self._last = (self._last + 1) % len(self._model.map.input_ids)
        self._destinations[robot] = self._model.map.input_ids[self._last]

    def _generate_output_path(self, robot: Robot[Cell]):
        if self.personal_rest:
            res = self.path_adder(
                robot, self._model.now,
                self.robot_type.time_to_put,
                self._model.map.outputs[robot.mail.destination], # type: ignore
                self.robots_rests[robot])
        else:
            res = self._add_path_for_closest_rest(
                robot,
                self._model.now,
                self.robot_type.time_to_put,
                self._model.map.outputs[robot.mail.destination], # type: ignore
            )
        self._robots_paths[robot].extend(res[0])
        self._robots_reserves[robot].extend(res[1])
        self._current[robot] = self._robots_reserves[robot].popleft()

    def _abort(self, time: float, robot: Robot[Cell]):
        yield self._model.timeout(time)
        robot.abort()

    def _next_states(self, state: State
                   ) -> typing.Iterable[tuple[State, float]]:
        if isinstance(self._model.map, OneWayMap):
            if self._model.map.can_go(state[0], state[1]):
                yield (state[0].get_next_on(state[1]), state[1]), self.robot_type.time_to_move
        else:
            if self._model.map.has(new_pos := state[0].get_next_on(state[1])):
                yield (new_pos, state[1]), self.robot_type.time_to_move
        for new_direction in Direction:
            if new_direction != state[1]:
                yield (state[0], new_direction),\
                    self.robot_type.time_to_turn*Direction.turn_count(state[1], new_direction)

    def _timed_edges(self, vertex: TimedVertex[State], time: float
                    ) -> typing.Iterable[PathSpan[TimedVertex[State]]]:
        for u, weight in self._next_states(vertex.vertex):
            for new_interval in self._reserves[u[0]]: # before new_interval
                new_state = TimedVertex(u, new_interval)
                min_time = time + weight
                if new_interval.prev.val is not None: # to not first interval
                    min_time = max(min_time, new_interval.prev.val.reserve_until+weight)
                if new_interval.val is not None: # to not last interval
                    max_time = new_interval.val.reserve_from
                else:
                    max_time = INF
                if vertex.interval.val is not None: # from not last interval
                    max_time = min(max_time, vertex.interval.val.reserve_from)
                if max_time < min_time:
                    continue
                yield PathSpan(vertex, new_state, min_time - weight, min_time)

    def _multi_distance(self, vs: tuple[Position, ...], time_between: float,
                       cur: tuple[TimedVertex[State], int]):
        if (self._avoid_puts and 
            ((cell := self._model.map[cur[0].vertex[0]]).input_id is not None
              or cell.output_id is not None) 
            and cur[0].vertex != vs[0]):
            avoid = self._avoid_puts
        else:
            avoid = 0
        ans = self._model.map.distance(cur[0].vertex[0], vs[cur[1]])
        for i in range(cur[1], len(vs)-1):
            ans += self._model.map.distance(vs[i], vs[i+1])
        return ans*self.robot_type.time_to_move + (time_between+0.01)*(len(vs)-cur[1]-1) + avoid

    def _timed_edges_for_multi(self, vs: tuple[Position, ...],
                              time_between: float,
                              v: tuple[TimedVertex[State], int],
                              time:float,
                              ) -> typing.Iterable[PathSpan[tuple[TimedVertex[State], int]]]:
            if self._count_ends[v[1]] == 4:
                return
            if v[0].vertex[0] == vs[v[1]]:
                if v[1] == len(vs) - 1:
                    return
                if self._reserves[v[0].vertex[0]] == v[0].interval:
                    self._count_ends[v[1]] += 1
                for i in self._timed_edges(v[0], time + time_between):
                    # if i.vertex.vertex[1] == v[0].vertex[1]: # optional, TODO
                    yield PathSpan(v, (i.vertex_to, v[1]+1), i.start, i.end)
            for i in self._timed_edges(v[0], time):
                yield PathSpan(v, (i.vertex_to, v[1]), i.start, i.end)

    def _find_path_for_state(self, start: TimedVertex[State], time: float, end: State
                  ) -> dict[TimedVertex[State], list[PathSpan[TimedVertex[State]]]]:
        data = dijkstra(self._timed_edges, start, time)
        return {
            v_end: list(restore_path(start, v_end, data))
            for interval in self._reserves[end[0]]
            if (v_end := TimedVertex(end, interval)) in data
        }

    def _find_path_for_position(self, start: TimedVertex[State], time: float, end: Position
                  ) -> dict[TimedVertex[State], list[PathSpan[TimedVertex[State]]]]:
        data = dijkstra(self._timed_edges, start, time)
        return {
            v_end: list(restore_path(start, v_end, data))
            for interval in self._reserves[end]
            for end_direction in Direction
            if (v_end := TimedVertex((end, end_direction), interval)) in data
        }
    
    def _find_path_for_rests(self, start: TimedVertex[State], time: float
                  ) -> list[PathSpan[TimedVertex[State]]]:
        data = dijkstra(self._timed_edges, start, time)
        min_time = INF
        min_end: TimedVertex[State] | None = None
        for position in self.rests:
            for direction in Direction:
                end = TimedVertex((position, direction), self._reserves[position])
                if end in data and data[end].end < min_time:
                    min_time = data[end].end
                    min_end = end
        if min_end is None:
            raise Exception("Unreachable path.")
        return list(restore_path(start, min_end, data))

    def _reserve_path(self, start_reserve: "TrueItem[Reservation]",
                     path: typing.Iterable[PathSpan[TimedVertex[State]]]
                     ) -> list[TrueItem[Reservation]]:
        start_reserve.remove()
        prev_reserve_from: float = start_reserve.val.reserve_from
        prev_be_from: float = start_reserve.val.be_from
        prev_interval = start_reserve.next
        result: list[TrueItem[Reservation]] = []
        for path_span in path:
            result.append(prev_interval.add_before(
                Reservation(prev_reserve_from, prev_be_from, path_span.start, path_span.end)))
            prev_reserve_from = path_span.start
            prev_be_from = path_span.end
            prev_interval = path_span.vertex_to.interval
        result.append(prev_interval.add_before(
            Reservation(prev_reserve_from, prev_be_from, INF, INF)))
        return result

    def _add_path(self, robot: Robot[Cell], start_time: float, end: State
                 ) -> tuple[list[PathSpan[TimedVertex[State]]], list[TrueItem[Reservation]]]:
        start = (robot.position, robot.direction)
        start_reserve = self._current[robot] # self._reserves[start[0]].prev
        if start_reserve.val.be_from > start_time:
            raise Exception(f"Wrong Path start: {robot} in {start} at {start_time} ")
        start_reserve.remove()
        timed_start = TimedVertex(start, start_reserve.next)
        timed_end = TimedVertex(end, self._reserves[end[0]])
        path = list(restore_path(timed_start, timed_end, dijkstra(self._timed_edges, timed_start, start_time)))
        return path, self._reserve_path(start_reserve, path)

    def _add_path_for_state(self, robot: Robot[Cell], start_time: float, time_between: float,
                           *vs: State
                           ) -> tuple[list[PathSpan[TimedVertex[State]]], list[TrueItem[Reservation]]]:
        start = (robot.position, robot.direction)
        start_reserve = self._current[robot] # self._reserves[start[0]].prev
        if start_reserve.val.be_from > start_time:
            raise Exception(f"Wrong Path start: {robot} in {start} at {start_time} ")
        start_reserve.remove()
        timed_start = TimedVertex(start, start_reserve.next)
        paths = [{timed_start: ([PathSpan(timed_start, timed_start, start_reserve.val.reserve_from, start_time-time_between)], timed_start)}]
        for i in range(len(vs)):
            paths.append({})
            for vertex_from, (path, _) in paths[i].items():
                res = self._find_path_for_state(vertex_from, path[-1].end + time_between, vs[i])
                for vertex_to, new_path in res.items():
                    if vertex_to not in paths[i+1] or paths[i+1][vertex_to][0][-1].end > new_path[-1].end:
                        paths[i+1][vertex_to] = (new_path, vertex_from)
        next_ = TimedVertex(vs[-1], self._reserves[vs[-1][0]])
        all_path: list[list[PathSpan[TimedVertex[State]]]] = []
        for i in range(len(vs), 0, -1):
            path = paths[i][next_]
            next_ = path[1]
            all_path.append(path[0])
        path = list(itertools.chain.from_iterable(reversed(all_path)))
        reserve = self._reserve_path(start_reserve, path)
        return path, reserve
    
    def _add_path_for_position_double_dijkstra(
            self, robot: Robot[Cell], start_time: float, time_between: float,
            for_min_time: Position, end: Position
            ) -> tuple[list[PathSpan[TimedVertex[State]]], list[TrueItem[Reservation]]]:
        start = (robot.position, robot.direction)
        start_reserve = self._current[robot]
        if start_reserve.val.be_from > start_time:
            raise Exception(f"Wrong Path start: {robot} in {start} at {start_time} ")
        start_reserve.remove()
        timed_start = TimedVertex(start, start_reserve.next)
        paths = [{timed_start: [PathSpan(timed_start, timed_start, start_reserve.val.reserve_from, start_time-time_between)]}]
        paths.append({})
        for vertex_from, path in paths[0].items():
            res = self._find_path_for_position(vertex_from, path[-1].end + time_between, for_min_time)
            for vertex_to, new_path in res.items():
                if vertex_to not in paths[1] or paths[1][vertex_to][-1].end > new_path[-1].end:
                    paths[1][vertex_to] = new_path
        
        min_time: float | None = None
        min_path: list[PathSpan[TimedVertex[State]]]
        min_from: TimedVertex[State]
        for vertex_from, path in paths[1].items():
            res = self._find_path_for_position(vertex_from, path[-1].end + time_between, end)
            for vertex_to, new_path in res.items():
                if min_time is None or path[-1].end < min_time:
                    min_time = path[-1].end
                    min_path = new_path
                    min_from = vertex_from
        if min_time is None:
            raise Exception("Unreachable path.")
        all_path = [paths[1][min_from], min_path] # type: ignore
        path = list(itertools.chain.from_iterable(all_path))
        reserve = self._reserve_path(start_reserve, path)
        return path, reserve

    def _add_path_for_closest_rest(
            self, robot: Robot[Cell], start_time: float, time_between: float,
            for_min_time: Position
            ) -> tuple[list[PathSpan[TimedVertex[State]]], list[TrueItem[Reservation]]]:
        start = (robot.position, robot.direction)
        start_reserve = self._current[robot]
        if start_reserve.val.be_from > start_time:
            raise Exception(f"Wrong Path start: {robot} in {start} at {start_time} ")
        start_reserve.remove()
        timed_start = TimedVertex(start, start_reserve.next)
        paths = [{timed_start: [PathSpan(timed_start, timed_start, start_reserve.val.reserve_from, start_time-time_between)]}]
        paths.append({})
        for vertex_from, path in paths[0].items():
            res = self._find_path_for_position(vertex_from, path[-1].end + time_between, for_min_time)
            for vertex_to, new_path in res.items():
                if vertex_to not in paths[1] or paths[1][vertex_to][-1].end > new_path[-1].end:
                    paths[1][vertex_to] = new_path
        
        min_time: float | None = None
        min_path: list[PathSpan[TimedVertex[State]]]
        min_from: TimedVertex[State]
        for vertex_from, path in paths[1].items():
            try:
                new_path = self._find_path_for_rests(vertex_from, path[-1].end + time_between)
            except:
                continue
            if min_time is None or path[-1].end < min_time:
                min_time = path[-1].end
                min_path = new_path
                min_from = vertex_from
        if min_time is None:
            raise Exception("Unreachable path.")
        all_path = [paths[1][min_from], min_path] # type: ignore
        path = list(itertools.chain.from_iterable(all_path))
        reserve = self._reserve_path(start_reserve, path)
        return path, reserve
    
    def _add_path_for_position(
            self, robot: Robot[Cell], start_time: float, time_between: float,
            *vs: Position
            ) -> tuple[list[PathSpan[TimedVertex[State]]], list[TrueItem[Reservation]]]:
        start = (robot.position, robot.direction)
        start_reserve = self._current[robot] # self._reserves[start[0]].prev
        if start_reserve.val.be_from > start_time:
            raise Exception(f"Wrong Path start: {robot} in {start} at {start_time} ")
        start_reserve.remove()
        timed_start = TimedVertex(start, start_reserve.next)
        self._count_ends = [0]*len(vs)
        data = a_star(lambda v, t: self._timed_edges_for_multi(vs, time_between, v, t),
                      lambda v: self._multi_distance(vs, time_between, v),
                      lambda v: v[0].vertex[0] == vs[-1]
                                and v[1] == len(vs) - 1
                                and v[0].interval == self._reserves[vs[-1]],
                      (timed_start, 0), start_time)
        min_ = INF
        min_end: tuple[TimedVertex[State], int] | None = None
        for direction in Direction:
            end = (TimedVertex((vs[-1], direction), self._reserves[vs[-1]]), len(vs)-1)
            if end in data and data[end].end < min_:
                min_ = data[end].end
                min_end = end
        if min_end is None:
            raise Exception("Unreachable path")
        path = list(
            PathSpan(span.vertex_from[0], span.vertex_to[0], span.start, span.end)
            for span in restore_path((timed_start, 0), min_end, data))
        reserve = self._reserve_path(start_reserve, path)
        return path, reserve
