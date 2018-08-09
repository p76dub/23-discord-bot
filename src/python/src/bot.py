# -*- coding: utf-8 -*-
# !/usr/env python3
import sqlite3

import discord

import re
import tempfile
import os

import adapter


class TwentyThreeBot(discord.Client):

    def __init__(self, conf):
        super(TwentyThreeBot, self).__init__()
        self.conf = conf
        self._commands = []
        self._adapter = adapter.SQLite3Adapter(conf["db"])
        self._load_commands()

    def _load_commands(self):
        self._commands = [
            AddCommand(self._adapter, self),
            CategoriesCommand(self._adapter, self),
            ConsultCommand(self._adapter, self),
            SearchCommand(self._adapter, self),
            DownloadCommand(self._adapter, self),
            PlaitCommand(self._adapter, self),
            RemoveCommand(self._adapter, self),
        ]
        self._commands.append(HelpCommand(self._adapter, self, self._commands))

    async def on_message(self, message):
        for _command in self._commands:
            await _command.match(message)

    async def on_ready(self):
        print("---------------")
        print("Started as {} ({})".format(self.user.name, self.user.id))
        print("---------------")


class AbstractCommand(object):

    COMMAND_PATTERN = re.compile(r"^.*$")
    CATEGORY_PATTERN = re.compile(r"^\[(\S+)\]$")
    COMMAND_NAME = "AbstractCommand"

    NOT_FOUND_MSG = "Je n'ai rien trouvé ! ;("
    ERROR_MSG = "Une erreur s'est produite ! :O"
    DOUBLE_MSG = "Je n'accepte pas les doublons !! >:("

    def __init__(self, adapter, client):
        self._adapter = adapter
        self._client = client

    async def match(self, msg):
        match = self.COMMAND_PATTERN.match(msg.content)
        if match:
            await self._do_match(match, msg)

    async def _do_match(self, match, msg):
        raise NotImplementedError()

    @staticmethod
    def help():
        return ""


class AddCommand(AbstractCommand):

    COMMAND_PATTERN = re.compile(r"^/23add\s(\S+)\s(.+)$")
    ADDED_MESSAGE = "Le fait a bien été ajouté ! :D"
    COMMAND_NAME = "23add"

    async def _do_match(self, match, msg):
        category, content = match.group(1, 2)
        try:
            self._adapter.add_fact(content, [category])
        except sqlite3.IntegrityError:  # FIXME: use a custom exception
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


class PlaitCommand(AbstractCommand):

    COMMAND_PATTERN = re.compile(r"/yop")
    COMMAND_NAME = "yop"

    async def _do_match(self, match, msg):
        await self._client.send_message(msg.channel, "plait !")

    @staticmethod
    def help():
        return "**/yop**\tAffiche juste \"plait !\""


if __name__ == '__main__':
    conf = {
        "db": os.environ["DB"],
        "token": os.environ["TOKEN"]
    }
    bot = TwentyThreeBot(conf)
    bot.run(conf["token"])
