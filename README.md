# 23-discord-bot
A discord bot that is able to manage facts in a database. Supported
operations are :

  * adding facts in categories
  * removing facts and categories
  * listing registered categories
  * download the current state as text file
  * help messages for each command
  * consulting registered facts in a category

## Installation
First, download the latest available version on github. To run this bot,
you need a python >= 3.5 environment with discord.py installed.

Then, create a discord application an get your token, you will need it
to run the bot. This token must be written in a configuration file,
located in the bot root folder with the following format :

    {
        "db": "location/to/sqlite/database",
        "token": "NDcyM...3lbV0I"
    }

Once it's done, you just need to launch the bot.py file !

## Available commands
**/23add CATEGORY FACT**: add a the fact **FACT** in he database,
associated the category **CATEGORY**. If one of them doesn't exist, it
will be created.

**/23consult CATEGORY \[LINE\]**: Display all facts related to
**CATEGORY**. If a line is provided, will only display the fact located
at the given line for the given category.

**/23search PATTERN**: Display all facts matching the given pattern.

**/23download**: Get a text file containing all facts and categories
currently registered.

**/23categories**: Get all registered categories.

**/23remove CATEGORY \[LINE\]**: If **LINE** is provided, remove the
located at line **LINE** in the category **CATEGORY**. Otherwise, remove
 the entire category.

**/23help \[COMMAND\]**: If **COMMAND** is provided, the command
displays a text describing the command behaviour. Otherwise, all
available commands are displayed with their respective help text.

