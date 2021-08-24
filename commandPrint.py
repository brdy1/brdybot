from brdybot import getCommands,commandHelp

commands = getCommands()
for command in list(commands.keys()):
    help = commandHelp([command])
    print(help)