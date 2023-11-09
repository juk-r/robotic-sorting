import typing
import simpy
import simpy.resources.store

from mail_factories.mail_factory import MailFactory
from structures import Mail

class SequenceAlwaysReadyMail(MailFactory):
    def __init__(self, env: simpy.Environment,
                 destinations: dict[int, typing.Iterable[int]]):
        super().__init__(env)
        self._last_id = 0
        self._destinations = {key: iter(val) for key, val in destinations.items()}

    @typing.override
    def __call__(self, input_id: int):
        return lambda: self._get_mail(input_id)

    def _get_mail(self, input_id: int):
        self._stores[input_id].put(Mail(self._last_id, next(self._destinations[input_id])))
        self._last_id += 1
        return self._stores[input_id].get()

    @typing.override
    def _putter(self):
        yield self._env.timeout(0)
