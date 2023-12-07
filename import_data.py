import json
import simpy
import simpy.resources.store
import typing

from structures import Map, Direction
from cell import Cell, MailInputGetter
from robot import RobotType, Robot
from brains import Brain

def import_json(file_path: str):
    with open(file_path) as file:
        return json.load(file)

def import_cell(env: simpy.Environment, 
                data: dict[str, typing.Any], 
                get_mail_input: MailInputGetter):
    free: bool = data["free"] if "free" in data else True
    input_id: int | None = data["inputId"] if "inputId" in data else None
    output_id: int | None = data["outputId"] if "outputId" in data else None
    charge_id: int | None = data["chargeId"] if "chargeId" in data else None
    return Cell(env, get_mail_input, input_id, output_id, charge_id, free)

def import_map(env: simpy.Environment,
               data: dict[str, typing.Any], 
               get_mail_input: MailInputGetter
               ) -> tuple[Map, float]:
    return Map([
        [import_cell(env, cell, get_mail_input) for cell in line] 
        for line in data['cells']
        ]), data['span']
    
def import_robot_type(data: dict[str, typing.Any], 
                      span: float) -> RobotType:
    return RobotType(span/data['speed'], data['timeToTurn'], 
                     data['TimeToPut'], data['TimeToTake'])

def import_direction(direction: str):
    match direction:
        case "up": return Direction.up
        case "left": return Direction.left
        case "down": return Direction.down
        case "right": return Direction.right
        case _: raise ValueError(f"{direction} is not direction")

def import_robot(env: simpy.Environment, 
                 brain: Brain, 
                 data: dict[str, typing.Any], 
                 span: float) -> Robot:
    return Robot(env, import_robot_type(data, span), brain, 
                 data['position'], data['direction'], data['charge'])

def import_state(env: simpy.Environment, 
                 data: dict[str, typing.Any], 
                 brain_from_map: typing.Callable[[Map], Brain], 
                 get_mail_input: MailInputGetter
                 ) -> tuple[Brain, Map, list[Robot]]:
    raise NotImplementedError()
    map, span = import_map(env, data['map'], get_mail_input)
    brain = brain_from_map(map)
    types = {type_['typeName']: import_robot_type(type_, span) 
                   for type_ in data['robotTypes']}
    robots = [import_robot(env, brain, 
                           robot.update(types[robot["robotType"]]), span)
              for robot in data['robots']]
    return brain, map, robots
