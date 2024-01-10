import simpy
import math
import json
import typing
import time

if typing.TYPE_CHECKING:
    from brains import Brain
    from structures import Map, Position, Direction
    from robot import Robot
    from typing import Any

BrainT = typing.TypeVar("BrainT", bound="Brain[Any, Any]", covariant=True)
RobotT = typing.TypeVar("RobotT", bound="Robot[Any]", covariant=True)
MapT = typing.TypeVar("MapT", bound="Map[Any]", covariant=True)

class Model(simpy.Environment, typing.Generic[MapT,  BrainT, RobotT]):
    map: MapT
    brain: BrainT
    robots: list[RobotT]
    def __init__(self):
        self._now: int
        super().__init__()
        self.robots = []

    def set_map(self, map: MapT): # type: ignore
        self.map = map

    def set_brain(self, brain: BrainT):  # type: ignore
        self.brain = brain

    def add_robot(self, robot: RobotT):  # type: ignore
        self.robots.append(robot)
        self.brain.new_robot(robot)

    def test(self, time: float, count: int) -> tuple[float, float]:
        """runs `count` times for `time`
        return: average, deviation for delivered mails"""
        results: list[float] = []
        last_cnt = self.brain.count
        for _ in range(count):
            self.run(self.now + time)
            results.append((self.brain.count - last_cnt))
            last_cnt = self.brain.count
        average = sum(results)/count
        std = math.sqrt(sum((i-average)**2 for i in results)/(count-1))
        print(average, std)
        return average, std

    def record(self, time_: int, file_name: str = 'record.json'):
        init_pos: list[tuple[int, int, int, int, bool]] = []
        for robot in self.robots:
            init_pos.append((0, robot.position.x, robot.position.y,
                            robot.direction.value, robot.mail is not None))
        data: list[list[tuple[int, int, int, int, bool]]] = [init_pos.copy()]
        t = time.time()
        try:
            for _ in range(1, time_+1):
                self.run(1+self.now)
                data.append([])
                for j, robot in enumerate(self.robots):
                    data[-1].append((0, robot.position.x, robot.position.y,
                                    robot.direction.value, robot.mail is not None))
                    # turn 180
                    if (robot.direction.value != data[-2][j][3] and
                            (robot.direction.value - data[-2][j][3]) % 2 == 0):
                        start = -1-2*robot.type.time_to_turn
                        data[start][j] = (robot.type.time_to_turn,
                                          data[start][j][1], data[start][j][2],
                                          (data[start][j][3]+1)%4, data[start][j][4])
                        mid = -1-robot.type.time_to_turn
                        data[mid][j] = (robot.type.time_to_turn,
                                          data[mid][j][1], data[mid][j][2],
                                          data[-1][j][3], data[mid][j][4])
                    # take
                    elif data[-1][j][4] and not data[-2][j][4]:
                        start = -1-robot.type.time_to_take
                        data[start][j] = (robot.type.time_to_take,
                                          data[start][j][1], data[start][j][2],
                                          data[start][j][3], True)
                    # put
                    elif not data[-1][j][4] and data[-2][j][4]:
                        start = -1-robot.type.time_to_put
                        data[start][j] = (robot.type.time_to_put,
                                          data[start][j][1], data[start][j][2],
                                          data[start][j][3], False)
                    # turn 90
                    elif data[-1][j][3] != data[-2][j][3]:
                        start = -1-robot.type.time_to_turn
                        data[start][j] = (robot.type.time_to_turn,
                                          data[start][j][1], data[start][j][2],
                                          data[-1][j][3], data[start][j][4])
                    # move
                    elif data[-1][j][1] != data[-2][j][1] or data[-1][j][2] != data[-2][j][2]:
                        start = -1-robot.type.time_to_move
                        data[start][j] = (robot.type.time_to_move,
                                          data[-1][j][1], data[-1][j][2],
                                          data[start][j][3], data[start][j][4])
        except Exception as exc:
            raise exc
        finally:
            print(f"took {time.time() - t} s")
            with open(file_name, 'w') as file:
                json.dump({'init': init_pos, 'data': data}, file)
