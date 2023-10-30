import json
import simpy
import simpy.resources.store
import typing

from structures import Map
from cell import Cell, MailInputGetter

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
