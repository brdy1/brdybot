import sys
import irc.bot
import requests
import pandas as pd
import psycopg2
import configparser


class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, client_id, token, channel):
        self.client_id = client_id
        self.token = token
        self.channel = '#' + channel

        # Get the channel id, we will need this for v5 API calls
        url = 'https://api.twitch.tv/kraken/users?login=' + channel
        headers = {'Client-ID': client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        r = requests.get(url, headers=headers).json()
        self.channel_id = r['users'][0]['_id']

        # Create IRC bot connection
        server = 'irc.chat.twitch.tv'
        port = 6667
        print('Connecting to ' + server + ' on port ' + str(port) + '...')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:'+token)], username, username)
        

    def on_welcome(self, c, e):
        print('Joining ' + self.channel)

        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)

    def on_pubmsg(self, c, e):

        # If a chat message starts with an exclamation point, try to run it as a command
        if e.arguments[0][:1] == '!':
            #store the command word after the exclamation
            command = e.arguments[0].split(' ')[0][1:]
            #store the parameters after the command word
            parameters = e.arguments[0].split(' ')[1:]
            print('Received command: ' + command + str(parameters))
            self.do_command(e, command, parameters)
        return

    def do_command(self, e, command, parameters):
        c = self.connection
        # procedure for the move command (fetching details of a pokemon move based on the currently selected generation).
        if command == "move":
            if len(parameters) > 1:
                moveName = ""
                for parameter in parameters:
                    moveName += parameter + " "
                #remove the extra space
                moveName = moveName.strip()
            else:
                moveName = parameters[0]
            if not moveName:
                c.privmsg(self.channel, "Incorrect usage. The !move command requires a move name as a parameter.")
            #moveInfo = fetchMoveInfo(self, moveName)
            moveName = moveName.lower()
            moveInfo = dbMoveInfo(self, moveName)
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, moveInfo)

        elif command == "gen":
            allowedGens = ['RB', '1', 'GS', '2', 'RS', '3', 'DP', '4', 'BW', '5', 'XY', '6', 'SM', '7', 'SS', '8']
            if len(parameters) != 1:
                c.privmsg(self.channel, "Incorrect usage. The !gen command requires one parameter - a two-letter abbreviation (RB, GS, RS, DP, BW, XY, SM, SS) or generation number.")
            try:
                generation = parameters[0].upper()
            except:
                pass
            if generation in allowedGens:
                url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
                headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
                r = requests.get(url, headers=headers).json()
                setGeneration(self, generation)
                c.privmsg(self.channel, "Generation was set to " + generation + ".")
            else:
                c.privmsg(self.channel, "Generation " + generation + " does not exist.")

        elif command == "mon":
            if len(parameters) <1:
                c.privmsg(self.channel, "Incorrect usage. The !mon command requires the name of a Pokemon as a parameter.")
            elif len(parameters) > 1:
                monName = ""
                for parameter in parameters:
                    monName += parameter + " "
                #remove the extra space, lol
                monName = monName.strip()
            elif parameters:
                monName = parameters[0]
            else:
                c.privmsg(self.channel, "Something went wrong with the !mon command. Oops!")
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            monInfo = fetchMonInfo(self, monName)
            c.privmsg(self.channel, monInfo)

        elif command == "ironmon":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'CLient-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, 'https://pastebin.com/L48bttfz')

        elif command == "challenges":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'CLient-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, 'I haven\'t got far, but I\'m doing a host of challenges, including a Pokemon Ironmon challenge, Diablo 2, Slay the Spire, and more! https://docs.google.com/spreadsheets/d/1BcEslzyAT4H6ZI7W6cwlGfYPCAB-0db-wxclFoO2B78')

        elif command == "commands":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'CLient-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, 'Available commands: !challenges, !ironmon, !mon <pokemon name>, !gen <gen#>, !move <move name>')

        # elif command == "move":
        #     url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
        #     headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        #     r = requests.get(url, headers=headers).json()
        #     c.privmsg(self.channel, r['display_name'] + ' channel title is currently ' + r['status'])

        # The command was not recognized
        # else:
        #     c.privmsg(self.channel, "Did not understand command: " + command)

def main():
    if len(sys.argv) != 5:
        print("Usage: twitchbot <username> <client id> <token> <channel>")
        sys.exit(1)

    username  = sys.argv[1]
    client_id = sys.argv[2]
    token     = sys.argv[3]
    channel   = sys.argv[4]

    bot = TwitchBot(username, client_id, token, channel)
    bot.start()

def fetchGeneration(self):
    config = configparser.ConfigParser()
    channel = self.channel.split('#')[1]
    configFilename = "../chatbot.ini"
    config.read(configFilename)
    generation = config[channel]["generation"]
    return generation

def dbMoveInfo(self, moveName):
    gen = fetchGeneration(self)
    moveList = executeSQL(f"SELECT m.movename, t.typename, mc.movecategoryname, m.movecontactflag, m.movepp, m.movepower, m.moveaccuracy, m.movepriority, m.movedescription FROM pokemon.move as m LEFT JOIN pokemon.type AS t ON m.typeid = t.typeid LEFT JOIN pokemon.movecategory AS mc ON m.movecategoryid = mc.movecategoryid WHERE LOWER(m.movename)='"+moveName+"' AND generationid="+gen)
    try:
        if moveList[3]:
            moveContact = "C"
        else:
            moveContact = "NC"
        info = str(moveList[0])+" ("+str(moveList[1])+", "+str(moveList[2])+", "+moveContact+") | PP: "+str(moveList[4])+" | Power: "+str(moveList[5])+" | Acc.: "+str(moveList[6])+" | Priority: "+str(moveList[7])+" | Summary: "+str(moveList[8])
    # except TypeError:
    #     try:
            
    #         moveList = executeSQL(f"SELECT m.movename, t.typename, mc.movecategoryname, m.movecontactflag, m.movepp, m.movepower, m.moveaccuracy, m.movepriority, m.movedescription FROM pokemon.move as m LEFT JOIN pokemon.type AS t ON m.typeid = t.typeid LEFT JOIN pokemon.movecategory AS mc ON m.movecategoryid = mc.movecategoryid WHERE LOWER(m.movename)='"+moveNoSpace+"' AND generationid="+gen)
    except TypeError:
        info = 'I could not find "' +moveName+'" in generation '+gen+'. Note that I prefer two separate words for older camelcase moves. (Use Bubble Beam, NOT BubbleBeam.).'
    print(info)
    return info

def fetchMoveInfo(self, moveName):
    gen = fetchGeneration(self)
    moveFilename = "../moves"+gen+".xlsx"
    df = pd.read_excel(moveFilename)
    moveName = (moveName).title()
    try:
        move = df.loc[df['name'] == moveName]
        moveName = move.iloc[0]['name']
        moveType = move.iloc[0]['type']
        pp = str(move.iloc[0]['pp'])
        category = str(move.iloc[0]['category'])
        power = str(move.iloc[0]['power'])
        accuracy = str(move.iloc[0]['accuracy'])
        description = move.iloc[0]['description']
        priority = str(move.iloc[0]['priority'])
        info = moveName+" ("+moveType+", "+category+") "+"| PP: "+pp+" | Power: "+power+" | Accuracy: "+accuracy+" | Priority: "+priority+" | Description: "+description
    except:
        info = 'I could not find move "' + moveName + '" in generation ' + gen + '.'
    return info

def fetchMonInfo(self, monName):
    gen = fetchGeneration(self)
    monFilename = "../pokemondata.xlsx"
    try:
        df = pd.read_excel(monFilename, gen)
        monName = monName.title()
        pokemon = df.loc[df['pokemonName'] == monName]
        dex = "#" + str(pokemon.iloc[0]['pokedex_number'])
        name = str(pokemon.iloc[0]['pokemonName']).title()
        type1 = str(pokemon.iloc[0]['Type1']).title()
        type2 = str(pokemon.iloc[0]['Type2']).title()
        if type2 != 'Nan':
            types = str(type1) + "/" + str(type2)
        else:
            types = type1
        capture = str(pokemon.iloc[0]['capturePercent'])
        levelRate = str(pokemon.iloc[0]['levelingRate'])
        bst = str(pokemon.iloc[0]['baseStatTotal'])
        if gen == 'RB':
            stats = str(pokemon.iloc[0]['hitPoints']) + " HP, " + str(pokemon.iloc[0]['attack']) + " Atk, " + str(pokemon.iloc[0]['defense']) + " Def, " + str(pokemon.iloc[0]['specialAttack']) + " Spec, " + str(pokemon.iloc[0]['speed']) + " Spe"
        else:
            stats = str(pokemon.iloc[0]['hitPoints']) + " HP, " + str(pokemon.iloc[0]['attack']) + " Atk, " + str(pokemon.iloc[0]['defense']) + " Def, " + str(pokemon.iloc[0]['specialAttack']) + " SpAtk, " + str(pokemon.iloc[0]['specialDefense']) + " SpDef, " + str(pokemon.iloc[0]['speed']) + " Spe"
        xpyield = str(pokemon.iloc[0]['expYield'])
        monInfo = dex + " " + name + " (" + types + ") | BST: " + bst + " | Capture %: " + capture + " | XP: " + xpyield + " | Lvl Rate: " + levelRate + " | Stats: " + stats
    except:
       monInfo = "I could not find " + monName + " in generation " + gen + "."
    return monInfo

def setGeneration(self, generation):
    generation = generation.upper()
    if generation == "RB":
        generation = 1
    elif generation == "GS":
        generation = 2
    elif generation == "RS":
        generation = 3
    elif generation == "DP":
        generation = 4
    elif generation == "BW":
        generation = 5
    elif generation == "XY":
        generation = 6
    elif generation == "SM":
        generation = 7
    elif generation == "SS":
        generation = 8
    config = configparser.ConfigParser()
    channel = self.channel.split('#')[1]
    config[channel] = {
        "ClientID": self.client_id,
        "Generation": generation
    }
    filename = channel + ".ini"
    with open(filename, 'w+') as configfile:
        config.write(configfile)

def databaseConfig(configfile="chatbot.ini",section="Database"):
    config = configparser.ConfigParser()
    config.read(configfile)
    db = {}
    if config.has_section(section):
        params = config.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in {1} file'.format(section,configfile))
    return db

def executeSQL(sql):
    conn = None
    params = databaseConfig()
    print("Connecting to database...")
    conn = psycopg2.connect(**params)
    with conn.cursor() as cur:
        cur.execute(sql)
        result = cur.fetchone()
    return result

if __name__ == "__main__":
    main()
