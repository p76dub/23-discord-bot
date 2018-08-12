# -*- coding: utf-8 -*-
# !/usr/env python3
import re
import tempfile
import os
import signal

import discord
from discord import ChannelType

import adapter


class TwentyThreeBot(discord.Client):
    """
    Main bot class. For command registering: use the :meth:`_load_commands`. The bot is relying
    on an Adapter for its commands.
    """
    VERSION = "0.2.1"

    def __init__(self, conf, adapter_class=adapter.SQLite3Adapter):
        """
        Create a new bot with the provided configuration (dict-like). If no adapter class is
        provided, the default one is :obj:`adapter.SQLite3Adapter`.

        :param conf: a dict-like object providing configuration
        :param adapter_class: a subclass of :obj:`adapter.Adapter`
        """
        super(TwentyThreeBot, self).__init__()
        self.conf = conf
        self._commands = []
        self._adapter = adapter_class(conf["db"])
        self._load_commands()

    def _load_commands(self):
        """
        This method is just a tool for registering new commands.
        """
        self._commands = [
            AddCommand(self._adapter, self),
            CategoriesCommand(self._adapter, self),
            ConsultCommand(self._adapter, self),
            SearchCommand(self._adapter, self),
            DownloadCommand(self._adapter, self),
            YopCommand(self._adapter, self),
            RemoveCommand(self._adapter, self),
            VersionCommand(self._adapter, self, self.VERSION)
        ]
        self._commands.append(HelpCommand(self._adapter, self, self._commands))

    async def on_message(self, message):
        """
        This method is called when a message is published on a channel. Each registered command
        is called with the message.

        :param message: the published message
        """
        for _command in self._commands:
            await _command.match(message)

    async def on_ready(self):
        """
        Called when the client (the bot) is connected to discord servers.
        """
        print("---------------")
        print("Started as {} ({})".format(self.user.name, self.user.id))
        print("---------------")

    async def stop(self):
        """
        Stop the bot as soon as possible.
        """
        for server in self.servers:
            for channel in server.channels:
                if channel.type == ChannelType.text:
                    await self.send_message(channel, "Je vais me coucher ! @+ !")
        self.close()
        self.logout()


class AbstractCommand(object):
    """
    Main class for future commands. It defines several constants (error messages, not found ...)
    The only things you need to redefine are :

        * the class attribute COMMAND_PATTERN, which must be a compiled regex
        * the class attribute COMMAND_NAME, (should match with the regex)
        * the _do_match method
        * the help static method, which should return a string

    """

    COMMAND_PATTERN = re.compile(r"^.*$")
    CATEGORY_PATTERN = re.compile(r"^\[(\S+)\]$")
    COMMAND_NAME = "AbstractCommand"

    NOT_FOUND_MSG = "Je n'ai rien trouvé ! ;("
    ERROR_MSG = "Une erreur s'est produite ! :O"
    DOUBLE_MSG = "Je n'accepte pas les doublons !! >:("

    def __init__(self, adapter, client):
        """
        Create a new AbstractCommand, with the provided adapter and client.

        :param adapter: a valid adapter
        :param client: a discord client
        """
        self._adapter = adapter
        self._client = client

    async def match(self, msg):
        """
        If the message content matches the command regex, then the :meth:`_do_match` method is
        called.

        :param msg: the published message
        """
        match = self.COMMAND_PATTERN.match(msg.content)
        if match:
            await self._do_match(match, msg)

    async def _do_match(self, match, msg):
        """
        Method called when the published message matches the command regex.

        :param match: a Match object
        :param msg: the original message
        """
        raise NotImplementedError()

    @staticmethod
    def help():
        """
        Called when you want a help message about the command.

        :return: an str
        """
        return ""


class AddCommand(AbstractCommand):
    """
    This command purpose is to add new facts to the database, in the provided category.
    Command is : /23add CATEGORY FACT
    If the message is successfully added, then all users are notified with the ADDED_MESSAGE.
    """

    COMMAND_PATTERN = re.compile(r"^/23add\s(\S+)\s(.+)$")
    ADDED_MESSAGE = "Le fait a bien été ajouté ! :D"
    COMMAND_NAME = "23add"

    async def _do_match(self, match, msg):
        category, content = match.group(1, 2)
        try:
            self._adapter.add_fact(content, [category])
        except adapter.DuplicateException:
            await self._client.send_message(msg.channel, self.DOUBLE_MSG)
        except Exception as e:
            await self._client.send_message(msg.channel, self.ERROR_MSG)
        else:
            await self._client.send_message(msg.channel, self.ADDED_MESSAGE)

    @staticmethod
    def help():
        return "**/23add CATEGORY FACT**\tAjouter un nouveau fait dans la base. Si la catégorie " \
               "n'existe pas, elle sera créée."


class ConsultCommand(AbstractCommand):
    """
    This command allows database consulting. The command is : /23consult CATEGORY [LINE]. With
    this command, users can display all registered facts for the provided category and, if a line is
     provided, displays the fact located at this line.
    """

    COMMAND_PATTERN = re.compile(r"^/23consult\s(\S+)(\s(\d)+)?$")
    COMMAND_NAME = "23consult"

    async def _do_match(self, match, msg):
        category, line_number = match.group(1, 3)
        if line_number is not None:
            line_number = int(line_number)

        returned = self._adapter.consult(category, line_number)

        if not returned:
            returned = [self.NOT_FOUND_MSG]
        else:
            returned = ["{}. {}".format(i + 1, r) for i, r in enumerate(returned)]
        await self._client.send_message(msg.channel, "\n".join(returned))

    @staticmethod
    def help():
        return "**/23consult CATEGORY [LINE]**\tConsulter l'ensemble des faits de la catégorie " \
               "CATEGORY. Si un numéro de ligne est spécifié, seul le fait occupant cette ligne " \
               "sera affiché."


class CategoriesCommand(AbstractCommand):
    """
    This command allows categories listing. Command is /23categories and display all registered
    categories.
    """

    COMMAND_PATTERN = re.compile(r"^/23categories$")
    COMMAND_NAME = "23categories"

    async def _do_match(self, match, msg):
        try:
            result = self._adapter.list_categories()
        except Exception as e:
            await self._client.send_message(msg.channel, self.ERROR_MSG)
        else:
            if not result:
                result = [self.NOT_FOUND_MSG]
            await self._client.send_message(msg.channel, " ".join(result))

    @staticmethod
    def help():
        return "**/23categories**\tAffiche l'ensemble des catégories connues."


class SearchCommand(AbstractCommand):
    """
    This commands allows users to search for a pattern in available facts and displays matching
    facts. The command is /23search PATTERN. Because the pattern is treated by the adapter,
    you should not assume that it can be a regex.

    Displayed results will highlight the pattern.
    """

    COMMAND_PATTERN = re.compile(r"^/23search\s(.+)$")
    COMMAND_NAME = "23search"

    async def _do_match(self, match, msg):
        pattern = match.group(1)
        result = self._adapter.search(pattern)
        if len(result) == 0:
            result = [self.NOT_FOUND_MSG]

        compiled_pattern = re.compile(pattern, re.IGNORECASE)
        result = "\n".join(result)

        def bold_and_underlined(_match):
            return "__***{}***__".format(_match.group(0))

        result = compiled_pattern.sub(bold_and_underlined, result)
        await self._client.send_message(msg.channel, result)

    @staticmethod
    def help():
        return "**/23search PATTERN**\tAfficher l'ensemble des faits qui contiennent la séquence " \
               "PATTERN."


class DownloadCommand(AbstractCommand):
    """
    The download command allows users to download the current state of the database as a text
    file with the following format :

        [category]
        1. fact ...
        ...
        i. fact ...
        [category]
        ...

    The command is /23download
    """

    COMMAND_PATTERN = re.compile(r"^/23download$")
    COMMAND_NAME = "23download"

    async def _do_match(self, match, msg):
        # Get all categories
        categories = self._adapter.list_categories()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as _fd:
            for category in categories:
                _fd.write("[{}]\n".format(category))

                facts = self._adapter.consult(category)
                for i, fact in enumerate(facts):
                    _fd.write("{}. {}\n".format(i + 1, fact))

                _fd.write("\n")
            filename = _fd.name

        await self._client.send_file(msg.channel, filename)
        os.remove(filename)

    @staticmethod
    def help():
        return "**/23download**\tObtenir la dernière version des données sous forme de fichier " \
               "texte."


class RemoveCommand(AbstractCommand):
    """
    The RemoveCommand allows users to remove a fact from a category or an entire category whether
    the line argument is provided or not.
    Command is : /23remove CATEGORY [LINE]
    """

    COMMAND_PATTERN = re.compile(r"^/23remove\s(\S+)(\s(\d)+)?$")
    FACT_REMOVED_MSG = "Le fait a été supprimé ! :D"
    CAT_REMOVED_MSG = "La catégorie a été supprimée ! :D"

    COMMAND_NAME = "23remove"

    async def _do_match(self, match, msg):
        category, line_number = match.group(1, 3)

        if line_number is not None:
            self._adapter.remove_fact(category, int(line_number))
            await self._client.send_message(msg.channel, self.FACT_REMOVED_MSG)
        else:
            self._adapter.remove_category(category)
            await self._client.send_message(msg.channel, self.CAT_REMOVED_MSG)

    @staticmethod
    def help():
        return "**/23remove CATEGORY [LINE]**\tSi LINE est spécifié, supprime le fait à la ligne " \
               "LINE de la catégorie CATEGORY. Sinon, supprime la catégorie CATEGORY (et les " \
               "faits associés)."


class HelpCommand(AbstractCommand):
    """
    Help command displaying all other commands help or, if a specific command is requested,
    this command's help.
    You can call the HelpCommand like this : /23help [COMMAND]

    Remember that, despite you are using /23help for calling the command, the command's name is
    23help (same for other commands).
    """

    COMMAND_PATTERN = re.compile(r"^/23help(\s(\S+))?$")
    COMMAND_NAME = "23help"

    def __init__(self, _adapter, client, commands):
        super(HelpCommand, self).__init__(_adapter, client)
        self._commands = commands

    async def _do_match(self, match, msg):
        command = match.group(2)
        print(command)
        if command is not None:
            for c in self._commands:
                if c.COMMAND_NAME == command:
                    await self._client.send_message(msg.channel, c.help())
        else:
            result = "\n".join([c.help() for c in self._commands])
            await self._client.send_message(msg.channel, result)

    @staticmethod
    def help():
        return "**/23help [COMMAND]**\tSi COMMAND est spécifié, affiche l'aide de la commande, " \
               "sinon affiche celle de toutes les commandes disponibles (y compris celle-ci)."


class YopCommand(AbstractCommand):
    """
    This is a little command requested by Marshall-Ange. It just displays "lait !".
    """

    COMMAND_PATTERN = re.compile(r"/yop")
    COMMAND_NAME = "yop"

    async def _do_match(self, match, msg):
        await self._client.send_message(msg.channel, "lait !")

    @staticmethod
    def help():
        return "**/yop**\tAffiche juste \"lait !\""


class VersionCommand(AbstractCommand):
    """
    A small command for obtaining the current bot version.
    """

    COMMAND_PATTERN = re.compile(r"/23version")
    COMMAND_NAME = "version"

    def __init__(self, adapter, client, version):
        super(VersionCommand, self).__init__(adapter, client)
        self._version = version

    async def _do_match(self, match, msg):
        await self._client.send_message(
            msg.channel,
            "Je tourne sur BotOS v{}".format(self._version)
        )


if __name__ == '__main__':
    import asyncio

    conf = {
        "db": os.environ["DB"],
        "token": os.environ["TOKEN"]
    }
    bot = TwentyThreeBot(conf)
    loop = asyncio.get_event_loop()

    def exit_gracefully():
        raise KeyboardInterrupt()

    loop.add_signal_handler(signal.SIGTERM, exit_gracefully)
    loop.add_signal_handler(signal.SIGINT, exit_gracefully)

    try:
        loop.run_until_complete(bot.start(conf["token"]))
    except KeyboardInterrupt:
        loop.run_until_complete(bot.stop())
    finally:
        loop.close()
