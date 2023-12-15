import typing

if typing.TYPE_CHECKING:
    from structures import Position
    from robot import Robot
    from cell import Cell

class ModellingException(BaseException):
    pass

class NotFreeCellException(ModellingException):
    def __init__(self, cell: "Cell"):
        super().__init__(f"{cell} is not free.")


class NotInputCellException(ModellingException):
    def __init__(self, cell: "Cell"):
        super().__init__(f"{cell} is not an input.")


class RobotWithMailException(ModellingException):
    def __init__(self, robot: "Robot"):
        super().__init__(f"{robot} already has a mail.")


class RobotWithoutMailException(ModellingException):
    def __init__(self, robot: "Robot"):
        super().__init__(f"{robot} does not have a mail to put.")


class PositionOutOfMapException(ModellingException):
    def __init__(self, position: "Position"):
        super().__init__(f"{position} is out of map.")

class NotRectangleMapException(ModellingException):
    def __init__(self):
        super().__init__("Map is not a rectangle.")


class DataImportException(BaseException):
    pass
