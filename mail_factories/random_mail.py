import typing
import random
import simpy

from structures import Mail
from mail_factories.mail_factory import MailFactory


class RandomMail(MailFactory):
    def __init__(self, env: simpy.Environment,
                 time_span: typing.Callable[[], float | int] | float,
                 input_id: typing.Callable[[], int] | typing.Sequence[int],
                 destination: typing.Callable[[], int] | typing.Sequence[int],):
        super().__init__(env)
        self._id = 0
        if isinstance(time_span, (float, int)):
            self._time_span = lambda: time_span
        else:
            self._time_span = time_span
        if isinstance(input_id, typing.Callable):
            self._input_id = input_id
        else:
            self._input_id = lambda: random.choice(input_id)
        if isinstance(destination, typing.Callable):
            self._destination = destination
        else:
            self._destination = lambda: random.choice(destination)

    @typing.override
    def _putter(self):
        while True:
            yield self._env.timeout(self._time_span())
            self._stores[self._input_id()].put(
                Mail(self._id, self._destination()))
            self._id += 1
