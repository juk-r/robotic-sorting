import dataclasses
import typing
import simpy

from structures import Mail
from mail_factories.mail_factory import MailFactory

class MailFromLog(MailFactory):
    @dataclasses.dataclass
    class MailLog:
        id: int
        input_id: int
        input_time: float
        destination: int

    def __init__(self, env: simpy.Environment, log: list[MailLog]):
        super().__init__(env)
        self._log = sorted(log, key=lambda m: m.input_time)

    @typing.override
    def _putter(self):
        time = self._env.now
        for mail in self._log:
            yield self._env.timeout(mail.input_time - time)
            self._stores[mail.input_id].put(Mail(mail.id, mail.destination))
            time = self._env.now
