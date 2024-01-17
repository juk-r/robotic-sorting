import abc
import collections
import typing
import simpy
import simpy.resources.store

class MailFactory(abc.ABC):
    """Abstract Mail Factory"""
    def __init__(self, env: simpy.Environment):
        self._env = env
        self._stores = collections.defaultdict[int, simpy.Store](
            lambda: simpy.Store(env))
        env.process(self._putter())

    def __call__(self, input_id: int):
        return self._stores[input_id].get

    @abc.abstractmethod
    def _putter(self) -> typing.Generator[simpy.Event, None, None]:
        pass
