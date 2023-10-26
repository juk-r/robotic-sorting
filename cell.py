import typing
import simpy
import simpy.resources.store

from exceptions import NotFreeCellException, NotInputCellException

MailInputGetter = typing.Callable[
                   [int],
                   typing.Callable[[], simpy.resources.store.StoreGet]]

class Cell(simpy.Resource):
    @property
    def free(self):
        return self._free
    @property
    def input_id(self):
        return self._input_id
    @property
    def output_id(self):
        return self._output_id
    @property
    def charge_id(self):
        return self._charge_id

    def __init__(self, env: simpy.Environment,
                 get_mail_input: MailInputGetter,
                 free: bool = True,
                 input_id: int | None = None,
                 output_id: int | None = None,
                 charge_id: int | None = None):
        super().__init__(env)
        self._env = env
        self._free = free
        self._input_id = input_id
        if input_id is not None:
            self._input = get_mail_input(input_id)
        else:
            self._input = None
        self._output_id = output_id
        self._charge_id = charge_id

    def request(self):
        if not self._free:
            raise NotFreeCellException(self)
        return super().request()

    def get_input(self):
        if self._input is None:
            raise NotInputCellException(self)
        return self._input()