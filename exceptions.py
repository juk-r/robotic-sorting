import typing

if typing.TYPE_CHECKING:
    from structures import Position, Mail
    from robot import Robot
    from cell import Cell

class ModellingException(BaseException):
    pass

class MovedToWall(ModellingException):
    def __init__(self, cell: "Cell"):
        super().__init__(f"{cell} is not free.")


class NotInputCell(ModellingException):
    def __init__(self, cell: "Cell"):
        super().__init__(f"{cell} is not an input.")


class RobotCollision(ModellingException):
    def __init__(self, cell: "Cell"):
        super().__init__(f"{cell} is reserved.")


class UnknownRequest(ModellingException):
    """
    internal, may be caused by
    wrong request handling by robots
    """
    pass


class DoubleMailTake(ModellingException):
    def __init__(self, robot: "Robot[typing.Any]"):
        super().__init__(f"{robot} already has a mail.")


class MailToPutAbsence(ModellingException):
    def __init__(self, robot: "Robot[typing.Any]"):
        super().__init__(f"{robot} does not have a mail to put.")


class IncorrectOutput(ModellingException):
    def __init__(self, mail: "Mail", cell: "Cell"):
        super().__init__(f"{cell} is not correct output for {mail}, expected {mail.destination}")


class PositionOutOfMap(ModellingException):
    def __init__(self, position: "Position"):
        super().__init__(f"{position} is out of map.")

class NotRectangleMap(ModellingException):
    def __init__(self):
        super().__init__("Map is not a rectangle.")


class InvalidDataFormat(BaseException):
    pass
