# 23-discord-bot
A discord bot that is able to manage facts in a database. Supported
operations are :

  * adding facts in categories
  * removing facts and categories
  * listing registered categories
  * download the current state as text file
  * help messages for each command
  * consulting registered facts in a category
  * adding multiple facts and categories with a provided text file

## Installation
First, download the latest available version on github. To run this bot,
you need a python >= 3.5 environment with discord.py installed.

Then, create a discord application an get your token, you will need it
to run the bot. The bot is using environment variables for configuration
purpose, like the database location and the discord application token.
By default, we use the MYSQLAdapter so you need to provide :

  * **DB** the database name (23facts for example)
  * **TOKEN** the discord bot token (you'll need to create a bot [here](https://discordapp.com/developers/applications/)) 
  * **HOST** where the database is located to (probably localhost)
  * **USER** the user the application will use to query the database (the default mysql user is `root`)
  * **PASSWORD** the password the application will use (By default there is no password for `root`)

If you haven't the mysql library installed, you can run the command `pip install mysql-connector-python==8.0.11`

If you want to use the SQLite3Adapter, you only need to provide :

  * **TOKEN** the discord application token
  * **DB** the sqlite3 filename

Once it's done, you just need to launch the bot.py file via your IDE or the command `python bot.py`

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

 **/23download**: Download the current state of the database as a text
 file.

 **/23upload**: If you tag an uploaded text file with this message, the
 bot will read it and add new facts and categories.

**/23help \[COMMAND\]**: If **COMMAND** is provided, the command
displays a text describing the command behaviour. Otherwise, all
available commands are displayed with their respective help text.

