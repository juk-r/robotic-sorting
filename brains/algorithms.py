import dataclasses
import typing

AgentT = typing.TypeVar("AgentT")
VertexT = typing.TypeVar("VertexT")
T = typing.TypeVar("T")
PriorityT = typing.TypeVar("PriorityT", int, float)


class PriorityQueue(typing.Protocol[T, PriorityT]):
    def __init__(self) -> None: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> typing.Iterator[tuple[T, PriorityT]]: ...
    def __contains__(self, val: T, /) -> bool: ...
    def __getitem__(self, val: T, /) -> PriorityT: ...
    def __setitem__(self, val: T, priority: PriorityT, /) -> None: ...


class MinHeap(typing.Generic[T, PriorityT]):
    def __init__(self, values: typing.Iterable[tuple[T, PriorityT]] = ()):
        self._values: list[tuple[T, PriorityT]] = []
        self._indexes: dict[T, int] = {}
        for val in values:
            self.enqueue(*val)

    def _swap(self, i: int, j: int):
        self._values[i], self._values[j] = self._values[j], self._values[i]
        self._indexes[self._values[i][0]] = i
        self._indexes[self._values[j][0]] = j

    def __len__(self):
        return len(self._values)

    def __getitem__(self, value: T, /) -> PriorityT:
        return self._values[self._indexes[value]][1]

    def __setitem__(self, value: T, priority: PriorityT):
        if value in self._indexes:
            self._values[i := self._indexes[value]] = (value, priority)
            self._swap_up(i)
            self._swap_down(i)
        else:
            self.enqueue(value, priority)
    
    def __contains__(self, value: T, /):
        return value in self._indexes

    def _swap_up(self, i: int):
        while i != 0 and self._values[(i-1)//2][1] > self._values[i][1]:
            self._swap(i, (i-1)//2)
            i = (i-1)//2

    def _swap_down(self, i: int):
        while 2*i+1 < len(self):
            if (2*i+2 < len(self)
                    and self._values[2*i+1][1] > self._values[2*i+2][1]
                    and self._values[2*i+2][1] < self._values[i][1]):
                self._swap(i, 2*i+2)
                i = 2*i+2
            elif self._values[2*i+1][1] < self._values[i][1]:
                self._swap(i, 2*i+1)
                i = 2*i+1
            else:
                break

    def enqueue(self, new_state: T, val: PriorityT):
        self._values.append((new_state, val))
        self._indexes[new_state] = len(self) - 1
        self._swap_up(len(self) - 1)

    def dequeue(self) -> tuple[T, PriorityT]:
        if len(self._values) == 0:
            raise StopIteration("Heap is empty")
        if len(self._values) == 1:
            del self._indexes[self._values[0][0]]
            return self._values.pop()
        self._swap(0, len(self) - 1)
        val = self._values.pop()
        del self._indexes[val[0]]
        self._swap_down(0)
        return val

    def __iter__(self) -> typing.Iterator[tuple[T, PriorityT]]:
        return self

    __next__ = dequeue


@dataclasses.dataclass(slots=True, eq=False)
class TrueItem(typing.Generic[T]):
    val: T
    prev: "Item[T]"
    next: "Item[T]"
    _removed: bool = False

    def add_before(self, val: T) -> "TrueItem[T]":
        item = TrueItem(val, self.prev, self)
        self.prev.next = item
        self.prev = item
        return item

    def remove(self):
        if self._removed:
            return
        self.next.prev, self.prev.next = self.prev, self.next
        self._removed = True
    
    @typing.override
    def __repr__(self):
        return repr(self.val)


class LinkedList(typing.Generic[T]):
    def __init__(self):
        self.next: Item[T] = self
        self.prev: Item[T] = self
        self.val: None = None

    def __iter__(self) -> typing.Iterator["Item[T]"]:
        current = self.next
        while isinstance(current, TrueItem):
            yield current
            current = current.next
        yield self

    def add_before(self, val: T) -> "TrueItem[T]":
        item = TrueItem(val, self.prev, self)
        self.prev.next = item
        self.prev = item
        return item
    
    @typing.override
    def __repr__(self):
        return repr(list(self)[:-1])

Item = TrueItem[T] | LinkedList[T]


@dataclasses.dataclass(frozen=True, slots=True)
class PathSpan(typing.Generic[VertexT]):
    vertex_from: VertexT
    vertex_to: VertexT
    start: float
    end: float
    @typing.override
    def __repr__(self):
        return f"({repr(self.vertex_from)}-{repr(self.vertex_to)}: {self.start}-{self.end})"


def dijkstra(edges: typing.Callable[[VertexT, float], typing.Iterable[PathSpan[VertexT]]],
             start: VertexT,
             start_time: float = 0,
             priorityQueue: type[PriorityQueue[VertexT, float]] = MinHeap
             ) -> dict[VertexT, PathSpan[VertexT]]:
    """
    Dijkstra's algorithm finds the shortest paths between given nodes and other nodes. 
    return: for each vertex, except start:
    - time when start go to it
    - time when come to it
    - vertex from which came.
    """
    queue = priorityQueue()
    queue[start] = start_time
    used = set[VertexT]()
    answer: dict[VertexT, PathSpan[VertexT]] = {}
    for vertex_from, time in queue:
        if vertex_from in used:
            continue
        used.add(vertex_from)
        for path_span in edges(vertex_from, time):
            if path_span.vertex_to in used:
                continue
            if path_span.vertex_to not in queue or queue[path_span.vertex_to] > path_span.end:
                queue[path_span.vertex_to] = path_span.end
                answer[path_span.vertex_to] = path_span
    return answer


def restore_path(start: VertexT, end: VertexT, 
                 data: dict[VertexT, PathSpan[VertexT]]
                 ) -> typing.Iterable[PathSpan[VertexT]]:
    vertex = end
    answer: list[PathSpan[VertexT]] = []
    while vertex != start:
        answer.append(data[vertex])
        vertex = data[vertex].vertex_from
    return reversed(answer)


def a_star(edges: typing.Callable[[VertexT, float], typing.Iterable[PathSpan[VertexT]]],
           distance: typing.Callable[[VertexT], float],
           end_check: typing.Callable[[VertexT], bool],
           start: VertexT,
           start_time: float,
           priorityQueue: type[PriorityQueue[VertexT, float]] = MinHeap
           ) -> dict[VertexT, PathSpan[VertexT]]:
    queue = priorityQueue()
    queue[start] = 0
    used = set[VertexT]()
    answer: dict[VertexT, PathSpan[VertexT]] = {start: PathSpan(start, start, 0, start_time)}
    for vertex_from, _ in queue:
        if end_check(vertex_from):
            break
        used.add(vertex_from)
        for path_span in edges(vertex_from, answer[vertex_from].end):
            if path_span.vertex_to in used:
                continue
            if path_span.vertex_to not in queue or path_span.end < answer[path_span.vertex_to].end:
                answer[path_span.vertex_to] = path_span
                queue[path_span.vertex_to] = path_span.end + distance(path_span.vertex_to)
    return answer