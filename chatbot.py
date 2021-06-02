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
        url, headers, r = getAPIVariables(self)
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
            c.privmsg(self.channel, moveInfo)

        elif command == "game":
            allowedGames = ['RB', 'Y', 'GS', 'C', 'RS', 'E', 'FRLG', 'DP', 'P', 'HGSS', 'BW', 'BW2', 'XY', 'ORAS', 'SM', 'USUM']
            if len(parameters) != 1:
                c.privmsg(self.channel, """Incorrect usage. The !gen command requires one parameter - 
                                        an abbreviation (RB, Y, GS, C, RS, E, FRLG, DP, P, HGSS, BW, BW2, XY, SM, USUM).
                                        Gen 8/SS is currently not supported, but it will be soon!""")
            try:
                game = parameters[0].upper()
            except:
                pass
            if game in allowedGames:
                setGame(self, game)
                c.privmsg(self.channel, "Game was set to " + game + ".")
            else:
                c.privmsg(self.channel, "Game '" + game + "' does not exist or is not supported.")

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
            monName = monName.title()
            monInfo = fetchMonInfo(self, monName)
            c.privmsg(self.channel, monInfo)

        elif command == "nature":
            if len(parameters) <1:
                c.privmsg(self.channel, "Incorrect usage. The !nature command requires the name of a nature to look up.")
            elif len(parameters) > 1:
                c.privmsg(self.channel, "Incorrect usage. The !nature command requires only the name of the nature to look up.")
            elif parameters:
                natureName = parameters[0]
                natureInfo = fetchNature(self, natureName)
                c.privmsg(self.channel, natureInfo)

        elif command == "ability":
            if len(parameters) <1:
                c.privmsg(self.channel, "Incorrect usage. The !ability command requires the name of an ability to look up.")
            elif len(parameters) > 1:
                abilityName = ""
                for parameter in parameters:
                    abilityName += parameter + " "
                #remove the extra space
                abilityName = abilityName.strip()
            elif parameters:
                abilityName = parameters[0]
            else:
                c.privmsg(self.channel, "Something went wrong with the !mon command. Oops!")
            abilityInfo = fetchAbility(self, abilityName)
            c.privmsg(self.channel, abilityInfo)

        elif command == "ironmon":
            c.privmsg(self.channel, 'https://pastebin.com/L48bttfz')

        elif command == "challenges":
            c.privmsg(self.channel, """I\'m challenging myself to complete various games,
                                    including a Pokemon Ironmon challenge, Diablo 2, Slay the Spire,
                                    and more! https://docs.google.com/spreadsheets/d/1BcEslzyAT4H6ZI7W6cwlGfYPCAB-0db-wxclFoO2B78""")

        elif command == "commands":
            c.privmsg(self.channel, "Available commands: !challenges, !ironmon, !mon <name>, !game <abbr>, !move <move>, !nature <nature>")

        # The command was not recognized
        # else:
        #     c.privmsg(self.channel, "Did not understand command: " + command)

def getAPIVariables(self):
    url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
    headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
    r = requests.get(url, headers=headers).json()
    return url, headers, r

def main():
    configFile = "../chatbot.ini"
    config = configparser.ConfigParser()
    config.read(configFile)
    username  = config['chatbot']['username']
    client_id = config['chatbot']['clientid']
    token     = config['chatbot']['token']
    channel   = config['chatbot']['channel']
    bot = TwitchBot(username, client_id, token, channel)
    bot.start()

def fetchNature(self, natureName):
    natureName = natureName.title()
    allowedNatures = str(executeSQL("SELECT nature.naturename from pokemon.nature"))
    if natureName in allowedNatures:
        neutral = executeSQL("SELECT n.neutralnatureflag FROM pokemon.nature n WHERE n.naturename = '"+natureName+"'")
        if 'True' in str(neutral):
            natureInfo = natureName + " is a neutral nature."
        elif 'False' in str(neutral):
            raisedStat = executeSQL("SELECT s.statname FROM pokemon.nature n LEFT JOIN pokemon.stat s ON n.raisedstatid = s.statid WHERE n.naturename = '"+natureName+"'")
            loweredStat = executeSQL("SELECT s.statname FROM pokemon.nature n LEFT JOIN pokemon.stat s ON n.loweredstatid = s.statid WHERE n.naturename = '"+natureName+"'")
            natureInfo = "+"+str(raisedStat[0][0])+"/"+"-"+str(loweredStat[0][0])
    else:
        natureInfo = "Could not find info for "+natureName+"."
    return natureInfo

def fetchAbility(self, abilityName):
    gen = fetchGeneration(self)
    abilityName = abilityName.title()
    allowedAbilities = str(executeSQL("SELECT ability.abilityname FROM pokemon.ability"))
    if abilityName in allowedAbilities:
        abilityTuple = executeSQL("""SELECT ga.abilitydescription FROM pokemon.generationability ga
                                    LEFT JOIN pokemon.ability ab ON ga.abilityid = ab.abilityid
                                    WHERE ab.abilityname = '"""+abilityName+"' AND ga.generationid <= """
                                    +gen+" ORDER BY ga.generationid DESC LIMIT 1")
        abilityInfo = abilityName + " (Gen "+gen+"): " + abilityTuple[0][0]
    else:
        abilityInfo = "Could not find info for "+abilityName+"."
    return abilityInfo

def fetchGeneration(self):
    config = configparser.ConfigParser()
    channel = self.channel.split('#')[1]
    configFilename = "../"+channel+".ini"
    config.read(configFilename)
    generation = config[channel]["generation"]
    return generation

def dbMoveInfo(self, moveName):
    gen = fetchGeneration(self)
    moveName = moveName.title()
    try:
        moveList = executeSQL("""SELECT m.movename, t.typename, mc.movecategoryname, m.movecontactflag,
                            m.movepp, m.movepower, m.moveaccuracy, m.movepriority, m.movedescription, m.generationid
                            FROM pokemon.move as m LEFT JOIN pokemon.type AS t ON m.typeid = t.typeid
                            LEFT JOIN pokemon.movecategory AS mc ON m.movecategoryid = mc.movecategoryid
                            WHERE m.movename = '""" + moveName + "' AND m.generationid = " + gen)
        moveList=moveList[0]
        if 'True' in str(moveList[0][3]):
            moveContact = "C"
        else:
            moveContact = "NC"
        info = str(moveList[0])+" ("+str(moveList[1])+", "+str(moveList[2])+", "+moveContact+") | PP: "+str(moveList[4])+" | Power: "+str(moveList[5])+" | Acc.: "+str(moveList[6])+" | Priority: "+str(moveList[7])+" | Summary: "+str(moveList[8])
    # except TypeError:
    #     try:
    #         moveList = executeSQL(f"SELECT m.movename, t.typename, mc.movecategoryname, m.movecontactflag, m.movepp, m.movepower, m.moveaccuracy, m.movepriority, m.movedescription FROM pokemon.move as m LEFT JOIN pokemon.type AS t ON m.typeid = t.typeid LEFT JOIN pokemon.movecategory AS mc ON m.movecategoryid = mc.movecategoryid WHERE LOWER(m.movename)='"+moveNoSpace+"' AND generationid="+gen)
    except:
        info = 'I could not find "' +moveName+'" in generation '+gen+'. Note that I prefer two separate words for older camelcase moves. (Use Bubble Beam, NOT BubbleBeam.).'
    return info

def fetchGame(self):
    config = configparser.ConfigParser()
    channel = self.channel.split('#')[1]
    configFilename = "../"+channel+".ini"
    config.read(configFilename)
    game = config[channel]["game"]
    return game

def fetchMonInfo(self, monName):
    gen = fetchGeneration(self)
    game = fetchGame(self)
    moveList = "Learns moves at "
    #note that I'm going to need to embed all of this in a 'try' and then return a different string upon error (nonetype,etc.)
    #fetch the info for a variant pokemon (mega, alolan, etc.)
    try:
        #check to see if the pokemon is a variant.
        monDexNameTypes = executeSQL("""SELECT DISTINCT mon.pokemonpokedexnumber,pv.pokemonvariantname,pv.pokemonvariantid,ty.typename 
                                        FROM pokemon.pokemonvariant pv LEFT JOIN pokemon.pokemon mon ON pv.pokemonid = mon.pokemonid 
                                        LEFT JOIN pokemon.pokemontype pt ON pv.pokemonvariantid = pt.pokemonvariantid 
                                        LEFT JOIN pokemon.type ty ON pt.typeid = ty.typeid
                                        WHERE pt.generationid = """+gen+
                                        " AND pv.pokemonvariantname = '"""+monName+
                                        "' AND pt.pokemonvariantid IS NOT NULL")
        #if it isn't a variant, do all of this ---
        if monDexNameTypes == []:
            #if no variant, search for a regular mon with fewer joins
            monDexNameTypes = executeSQL("""SELECT DISTINCT mon.pokemonpokedexnumber,mon.pokemonname,ty.typename,mon.pokemonid
                                            FROM pokemon.pokemon mon LEFT JOIN pokemon.pokemontype pt 
                                            ON mon.pokemonid = pt.pokemonid LEFT JOIN pokemon.type ty 
                                            ON pt.typeid = ty.typeid 
                                            WHERE mon.pokemonname = '"""+monName+"' AND pt.pokemonvariantid IS NULL")
            #pull the pokemon pokedex number from the results
            dex = str(monDexNameTypes[0][0])
            #pull the id of the pokemon from the pokemon table for later queries
            id = str(monDexNameTypes[0][3])
            #retrieve and calculate the BST
            monBST = executeSQL("""SELECT SUM(ps.pokemonstatvalue) bst,ps.generationid gen FROM pokemon.pokemonstat ps
                                    LEFT JOIN pokemon.pokemon mon ON ps.pokemonid = mon.pokemonid
                                    WHERE mon.pokemonpokedexnumber ="""+dex+""" AND ps.pokemonvariantid IS NULL AND ps.generationid <= """+gen+
                                    " GROUP BY gen ORDER BY gen DESC LIMIT 1")
            #if there is more than one type in the db, store as (Type1/Type2)
            if len(monDexNameTypes) > 1:
                types = "("+str(monDexNameTypes[0][2])+"/"+str(monDexNameTypes[1][2])+")"
            #otherwise, store as (Type)
            else:
                types = "("+str(monDexNameTypes[0][2])+")"
            moves = executeSQL("""SELECT DISTINCT mv.movename,pm.pokemonmovelevel FROM pokemon.pokemonmove pm 
                                    LEFT JOIN pokemon.move mv ON pm.moveid = mv.moveid 
                                    LEFT JOIN pokemon.gamegroup gg ON pm.gamegroupid = gg.gamegroupid 
                                    WHERE pm.pokemonid ="""+id+""" AND pokemonmovelevel > 1 
                                    AND gg.gamegroupabbreviation ='"""+game+"""' 
                                    ORDER BY pm.pokemonmovelevel ASC""")
            xp = executeSQL("""SELECT DISTINCT xp.experienceyieldvalue,xp.generationid FROM pokemon.pokemonexperienceyield xp 
                                LEFT JOIN pokemon.pokemon mon ON xp.pokemonid = mon.pokemonid
                                WHERE mon.pokemonid ="""+id+""" AND xp.generationid <= """+gen+""" 
                                AND xp.pokemonvariantid IS NULL
                                ORDER BY generationid ASC LIMIT 1""")
            xp=str(xp[0][0])
            evoArray = executeSQL("""SELECT DISTINCT mon.pokemonname, pel.pokemonevolutionlevel,
                                    i.itemname, l.locationname, pe.evolutiontypeid, pes.pokemonevolutionuniquestring, m.movename, gg.generationid
                                    FROM pokemon.pokemonevolution pe
                                    LEFT JOIN pokemon.pokemon mon ON pe.targetpokemonid = mon.pokemonid
                                    LEFT JOIN pokemon.pokemonevolutionlevel pel ON pe.pokemonevolutionid = pel.pokemonevolutionid
                                    LEFT JOIN pokemon.pokemonevolutionmove pem ON pe.pokemonevolutionid = pem.pokemonevolutionid
                                    LEFT JOIN pokemon.move m ON pem.moveid = m.moveid
                                    LEFT JOIN pokemon.pokemonevolutionitem pei ON pe.pokemonevolutionid = pei.pokemonevolutionid
                                    LEFT JOIN pokemon.item i ON pei.itemid = i.itemid
                                    LEFT JOIN pokemon.pokemonevolutionlocation ploc ON pe.pokemonevolutionid = ploc.pokemonevolutionid
                                    LEFT JOIN pokemon.location l ON ploc.locationid = l.locationid
                                    LEFT JOIN pokemon.gamegroup gg ON pe.gamegroupid = gg.gamegroupid
                                    LEFT JOIN pokemon.pokemonevolutionstring pes ON pe.pokemonevolutionid = pes.pokemonevolutionid
                                    WHERE pe.basepokemonid = """+id+""" AND gg.generationid <="""+gen+""" ORDER BY generationid ASC LIMIT 1""")
            evoInfo = getEvoInfo(evoArray)
            #LEFT JOIN pokemon.pokemonvariant pv ON pe.targetpokemonvariantid = pv.pokemonvariantid
        else:
            #for DB purposes, the variantid is the unique identifier of the pokemon.
            #once we know this, we can use it to easily fetch BST, moves, and other attributes  
            print(monDexNameTypes)
            variant = str(monDexNameTypes[0][2])
            #fetch move names + move levels for the pokemon in the generation, not including starting moves (lvl 1) and TM moves
            moves = executeSQL("""SELECT DISTINCT mv.movename,pm.pokemonmovelevel FROM pokemon.pokemonmove pm 
                                    LEFT JOIN pokemon.move mv ON pm.moveid = mv.moveid 
                                    LEFT JOIN pokemon.gamegroup gg ON pm.gamegroupid = gg.gamegroupid 
                                    WHERE pm.pokemonvariantid ="""+variant+""" AND pokemonmovelevel > 1 
                                    AND gg.gamegroupabbreviation ='"""+game+"""' 
                                    ORDER BY pm.pokemonmovelevel ASC""")
            monBST = executeSQL("""SELECT SUM(ps.pokemonstatvalue) bst,ps.generationid gen FROM pokemon.pokemonstat ps
                                    LEFT JOIN pokemon.pokemonvariant pv ON ps.pokemonvariantid = pv.pokemonvariantid
                                    WHERE pv.pokemonvariantid ="""+variant+""" AND ps.generationid <= """+gen+
                                    " GROUP BY gen ORDER BY gen DESC LIMIT 1")
            xp = executeSQL("""SELECT DISTINCT xp.experienceyieldvalue,xp.generationid FROM pokemon.pokemonexperienceyield xp 
                                LEFT JOIN pokemon.pokemonvariant pv ON xp.pokemonvariantid = pv.pokemonvariantid
                                WHERE pv.pokemonvariantid ="""+variant+""" AND xp.generationid <= """+gen+"""
                                ORDER BY generationid ASC LIMIT 1
            """)
            xp=str(xp[0][0])
            evoArray = executeSQL("""SELECT DISTINCT mon.pokemonvariantname, pel.pokemonevolutionlevel,
                                    i.itemname, l.locationname, pe.evolutiontypeid, pes.pokemonevolutionuniquestring, m.movename, gg.generationid
                                    FROM pokemon.pokemonevolution pe
                                    LEFT JOIN pokemon.pokemonvariant mon ON pe.targetpokemonvariantid = mon.pokemonvariantid
                                    LEFT JOIN pokemon.pokemonevolutionlevel pel ON pe.pokemonevolutionid = pel.pokemonevolutionid
                                    LEFT JOIN pokemon.pokemonevolutionmove pem ON pe.pokemonevolutionid = pem.pokemonevolutionid
                                    LEFT JOIN pokemon.move m ON pem.moveid = m.moveid
                                    LEFT JOIN pokemon.pokemonevolutionitem pei ON pe.pokemonevolutionid = pei.pokemonevolutionid
                                    LEFT JOIN pokemon.item i ON pei.itemid = i.itemid
                                    LEFT JOIN pokemon.pokemonevolutionlocation ploc ON pe.pokemonevolutionid = ploc.pokemonevolutionid
                                    LEFT JOIN pokemon.location l ON ploc.locationid = l.locationid
                                    LEFT JOIN pokemon.gamegroup gg ON pe.gamegroupid = gg.gamegroupid
                                    LEFT JOIN pokemon.pokemonevolutionstring pes ON pe.pokemonevolutionid = pes.pokemonevolutionid
                                    WHERE pe.basepokemonvariantid = """+variant+""" AND gg.generationid <="""+gen+""" ORDER BY generationid ASC LIMIT 1""")
            evoInfo = getEvoInfo(evoArray)
            #if the pokemon has more than one type, store the types as a string surrounded by parens with a '/' between
            if len(monDexNameTypes) > 1:
                types = "("+str(monDexNameTypes[0][3])+"/"+str(monDexNameTypes[1][3])+")"
            #otherwise, store the type as a string with parens
            else:
                types = "("+str(monDexNameTypes[0][3])+")"
        #fetch the list of move levels and store them in a str var
        for move in moves:
                moveList += str(move[1])+", "
        moveList = moveList[0:len(moveList)-2]
        name = str(monDexNameTypes[0][1])
        print(str(monDexNameTypes))
        dex = str(monDexNameTypes[0][0])
        print("BST:"+str(monBST))
        monBST = str(monBST[0][0])
        monInfo = "#"+dex+" "+name+" "+types+" | XP: "+xp+" | BST: "+monBST+" | "+evoInfo+" | "+moveList
    except:
        monInfo = "I was not able to find " +monName+" in generation "+gen+"."
    return monInfo

def getEvoInfo(evoArray):
            if evoArray == []:
                evoInfo = "Does not evolve"
            else:
                evoMon = str(evoArray[0][0])
                evoLevel = str(evoArray[0][1])
                evoItem = str(evoArray[0][2])
                evoLocation = str(evoArray[0][3])
                evoType = evoArray[0][4]
                evoUnique = str(evoArray[0][5])
                evoMove = str(evoArray[0][6])
                evoInfo = "Evolves into " + evoMon
                if evoType == 2 or evoType == 11:
                    evoInfo += " via trade"
                elif evoType == 3:
                    evoInfo += " via high friendship"
                elif evoType == 12:
                    evoInfo += " as a female "
                elif evoType == 13:
                    evoInfo += " as a male "
                elif evoType == 16:
                    evoInfo += " during the day"
                elif evoType == 17:
                    evoInfo += " at night"
                elif evoType == 20:
                    evoInfo += " in the rain"
                elif evoType == 21:
                    evoInfo += " via high beauty"
                if not evoLevel == 'None':
                    evoInfo += " at level "+evoLevel
                if not evoItem == 'None':
                    if evoType == 4:
                        evoInfo += " after being exposed to a " + evoItem
                    elif evoType == 10 or evoType == 11:
                        evoInfo += " while holding a " + evoItem
                if not evoLocation == 'None':
                    evoInfo += " at the " + evoLocation
                if not evoMove == 'None':
                    evoInfo += " while knowing " + evoMove
                if not evoUnique == 'None':
                    evoInfo += ": " + evoUnique
            return evoInfo

def setGame(self, game):
    game = game.upper()
    channel = self.channel.split('#')[1]
    config = configparser.ConfigParser()
    if game == "RB" or game == "Y":
        generation = 1
    elif game == "GS" or game == "C":
        generation = 2
    elif game == "RS" or game == "E" or game == "FRLG":
        generation = 3
    elif game == "DP" or game == "P" or game == "HGSS":
        generation = 4
    elif game == "BW" or game == "BW2":
        generation = 5
    elif game == "XY" or game == "ORAS":
        generation = 6
    elif game == "SM" or game == "USUM" or game == "LG":
        generation = 7
    elif game == "SS":
        generation = 8
    else:
        pass
    config[channel] = {
        "clientid": self.client_id,
        "generation": generation,
        "game": game
    }
    filename = "../" + channel + ".ini"
    with open(filename, 'w+') as configfile:
        config.write(configfile)

def databaseConfig(configfile="../chatbot.ini",section="database"):
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
        print("Executing: "+sql)
        result = cur.fetchall()
    return result

if __name__ == "__main__":
    main()
