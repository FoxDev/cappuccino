#  This file is part of cappuccino.
#
#  cappuccino is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  cappuccino is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with cappuccino.  If not, see <https://www.gnu.org/licenses/>.

import re

import irc3
from irc3.plugins.command import command
from sqlalchemy import Column, MetaData, String, Table, func


@irc3.plugin
class Seen(object):
    requires = [
        'irc3.plugins.command',
        'plugins.botui',
        'plugins.database'
    ]

    metadata = MetaData()
    triggers = Table('triggers', metadata,
                     Column('trigger', String, nullable=False),
                     Column('channel', String, nullable=False),
                     Column('response', String, nullable=False))

    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.database
        self.metadata.create_all(self.db)

    def _get_trigger(self, channel: str, trigger: str):
        stmnt = self.triggers.select(). \
            where(func.lower(self.triggers.c.trigger) == trigger.lower()). \
            where(func.lower(self.triggers.c.channel) == channel.lower())

        return self.db.execute(stmnt).scalar()

    def _set_trigger(self, channel: str, trigger: str, text: str):
        if self._get_trigger(channel, trigger):
            stmnt = self.triggers.update(). \
                where(func.lower(self.triggers.c.trigger) == trigger.lower()). \
                where(func.lower(self.triggers.c.channel) == channel.lower()).values(response=text)

            self.db.execute(stmnt)
            return

        self.db.execute(self.triggers.insert().values(channel=channel, trigger=trigger, response=text))

    def _delete_trigger(self, channel: str, trigger: str) -> bool:
        stmnt = self.triggers.delete(). \
            where(func.lower(self.triggers.c.trigger) == trigger.lower()). \
            where(func.lower(self.triggers.c.channel) == channel.lower()). \
            returning(self.triggers.c.trigger)

        return self.db.execute(stmnt).scalar() is not None

    @command(permission='view')
    def trigger(self, mask, target, args):
        """Manages predefined responses to message triggers.

            %%trigger (set <trigger> <response>... | del <trigger> | list)
        """

        if not target.startswith('#'):
            return 'This command can only be used in channels.'

        if (args['set'] or args['del']) and not self.bot.is_chanop(target, mask.nick):
            return 'Only channel operators may modify channel triggers.'

        trigger = args['<trigger>']
        if args['set']:
            self._set_trigger(target, trigger, ' '.join(args['<response>']))
            return f'Trigger \'{trigger}\' set.'

        if args['del']:
            return f'Deleted trigger \'{trigger}\'.' if self._delete_trigger(target, trigger) else 'No such trigger.'

        if args['list']:
            trigger_list = [row[0] for row in self.db.execute(self.triggers.select())]
            if trigger_list:
                trigger_list = ', '.join(trigger_list)
                return f'Available triggers for {target}: {trigger_list}'

            return f'No triggers available for {target}'

    @irc3.event(irc3.rfc.PRIVMSG)
    def on_privmsg(self, target, event, mask, data):
        if mask.nick == self.bot.nick or event == 'NOTICE':
            return

        triggers = re.search(r':([A-Za-z]+)', data)
        if not triggers:
            return

        triggers = set(triggers.groups()[:3])
        responses = []
        for trigger in triggers:
            response = self._get_trigger(target, trigger)
            trigger = self.bot.format(trigger.lower(), color=self.bot.color.PURPLE, reset=True)
            if response is not None:
                responses.append(f'[{trigger.lower()}] {response}')

        for response in responses:
            self.bot.privmsg(target, response)