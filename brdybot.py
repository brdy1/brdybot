#this is for opening the configuration file
import configparser
#this is for connecting to IRC
import socket
import irc
import json
import requests
#this is for connecting to the postgres database
import psycopg2
#this is for doing cute equations
import math
#for eventual multithreading for additional channels
import threading
#traceback is for error handling/printing so i can figure out what went wrong
import traceback
#sleep is so the bot won't overload during listening
from time import sleep

def main():
    config = configparser.ConfigParser()
    file = "../chatbot.ini"
    config.read(file)
    channels = config['chatbot']['userlist']
    channelList = channels.split(",")
    conn, token, user, readbuffer, server = connectionVariables()
    for channel in channelList:
        channel = channel.strip()
        print(channel)
        threading.Thread(target=ircListen, args=(conn, token, user, channel, server)).start()

#set variables for connection
def connectionVariables():
    connection_data = ('irc.chat.twitch.tv', 6667)
    token = getToken()
    botName = "brdybot"
    readbuffer = ''
    server = socket.socket()
    return connection_data, token, botName, readbuffer, server

def getToken():
    config = configparser.ConfigParser()
    file = "../chatbot.ini"
    config.read(file)
    token = config['chatbot']['token']
    return token

#establish connection
def ircListen(conn, token, botName, channel, server):
    config = configparser.ConfigParser()
    file = "../chatbot.ini"
    config.read(file)
    #joining the channel
    server = socket.socket()
    server.connect(conn)
    server.send(bytes('PASS ' + token + '\r\n', 'utf-8'))
    server.send(bytes('NICK ' + botName + '\r\n', 'utf-8'))
    server.send(bytes('JOIN #' + channel + '\r\n', 'utf-8'))
    #listening loop
    while True:
        response = server.recv(2048).decode('utf-8')
        if len(response) == 0:
            break
        print(response)

        if "PING" in str(response):
            pong = str(response).replace("PING","PONG")
            server.send(bytes(pong, 'utf-8'))
            server.send(bytes('PONG\r\n', 'utf-8'))
            print("Sent a PONG.")
        else:
            #fetch the username from the response
            try:
                print(response)
                username = str(response).split('!',1)[0][1:]
                print(username)
            #split the response to pull only the part we want for message extraction
                try:
                    splitResp = str(response).split(':')[2]+str(response).split(':')[3]
                except:
                    splitResp = str(response).split(':')[2]
            #extract only the message of the response, not including special ending characters
                userMessage = splitResp[0:len(splitResp)-2]
            #print what was in the chat
                print(username + ": " + userMessage)
            except Exception:
                traceback.print_exc()
                userMessage = " "
            operators = config[channel]['operators']
            command = userMessage.split(" ")[0].lower()
            parameters = userMessage.split(" ")[1:]
            permissions = (username in operators) or channel == 'brdybot'
            message = None
            try:
                if userMessage[0] == "!" and permissions:
                    print("Received the " + command + " command. Parameters: " + str(parameters))
                    if command == "!mon":
                        try:
                            monName = ""
                            for parameter in parameters:
                                monName += parameter + " "
                            monName = monName[:len(monName)-1]
                            message = getMonInfo(monName,channel)
                        except Exception:
                            traceback.print_exc()
                            gen = getGeneration(channel)
                            message = "Could not find Pokemon '" +monName.title()+ "' in generation "+gen+"."
                    elif command == "!move":
                        try:
                            moveName = ""
                            for parameter in parameters:
                                moveName += parameter + " "
                            moveName = moveName[:len(moveName)-1]
                        except Exception:
                            traceback.print_exc()
                        message = getMoveInfo(moveName,channel)
                    elif command == "!ability":
                        try:
                            abilityName = ""
                            for parameter in parameters:
                                abilityName += parameter + " "
                            abilityName = abilityName[:len(abilityName)-1]
                            message = getAbilityInfo(abilityName,channel)
                        except Exception:
                            traceback.print_exc()
                            gen = getGeneration(channel)
                            message = "Could not find ability '" +abilityName+ "' in generation "+gen+"."
                    elif command == "!nature":
                        try:
                            natureName = ""
                            for parameter in parameters:
                                natureName += parameter + " "
                            natureName = natureName[:len(natureName)-1]
                            message = getNatureInfo(natureName)
                        except Exception:
                            traceback.print_exc()
                            gen = getGeneration(channel)
                            message = "Could not find nature '" +natureName+ ".'"
                    elif command == "!weak":
                        try:
                            monName = ""
                            for parameter in parameters:
                                monName += parameter + " "
                            monName = monName[:len(monName)-1]
                            message = getWeaknessInfo(monName,channel)
                        except Exception:
                            traceback.print_exc()
                    elif command == "!pokegame" and username == channel:
                        message = setGame(parameters, channel, server)
                    elif command == "!join" and channel == "brdybot":
                        message = None
                        message = addClient(conn,token,botName,username,server)
                    elif command == "!leave" and channel == "brdybot":
                        message = removeClient(username)
                    elif command == "!pokecom":
                        commands = "!pokecom, !mon, !move, !ability, !nature, !weak, !pokegame, !botinfo"
                        message = "Available commands are " + commands + "."
                    elif command == "!botinfo":
                        message = "https://github.com/brdy1/brdybot"
                    if message:
                        chatMessage(message,channel,server)
            except Exception:
                traceback.print_exc()
        sleep(1)

def addClient(conn, token, botName, username, server):
    config = configparser.ConfigParser()
    file = "../chatbot.ini"
    config.read(file)
    userlist = config['chatbot']['userlist']
    #checks to see if username is in the channel's userlist in the config file
    if not username in userlist:
        userlist = userlist + ", " + username
        config['chatbot']['userlist'] = userlist
        with open(file, 'w+') as configfile:
            config.write(configfile)
        message = "You have been successfully added to the channel list."
        threading.Thread(target=ircListen, args=(conn, token, botName, username, server))
    else:
        message = "I should be operating in your channel. If I'm not, send a message to brdy to correct the error."
    return message

def removeClient(username):
    config = configparser.ConfigParser()
    file = "../chatbot.ini"
    config.read(file)
    userlist = config['chatbot']['userlist']
    #replaces the comma separated username with 1 comma to ensure no parts of names are replaced (ie brdy being replaced inside brdybot)
    if username in userlist:
        userlist.replace(","+username+",",",")
        message = "Your channel has been successfully removed from the channel list."
    else:
        message = "Something went wrong. You are not on the channel list. If you think this is incorrect, send a message to brdy to correct the error."
    return message

def getMoveID(moveName):
    moveName = moveName.title()
    moveName = moveName.replace("'","''")
    moveName = moveName.replace("'S","'s")
    moveID = performSQL("""SELECT mv.moveid FROM pokemon.move mv
                                WHERE mv.movename = '"""+moveName+"'")
    try:
        moveID = str(moveID[0][0])
    except Exception:
        if moveID == []:
            moveID = performSQL("""SELECT mn.moveid FROM pokemon.movenickname mn
                                    WHERE mn.movenickname = '"""+moveName+"'")
            moveID = str(moveID[0][0])
        else:
            traceback.print_exc()
    return moveID

def getMonID(monName):
    monName = monName.title()
    #farfetch'd and sirfetch'd exceptions
    monName = monName.replace("'D","''d")
    #this section fetches the pokemonid from the database and indicates to later queries whether it's a base or variant pokemon
    monID = performSQL("""SELECT DISTINCT mon.pokemonid FROM pokemon.pokemon mon 
                            WHERE mon.pokemonname = '"""+monName+"""' LIMIT 1""")
    try:
        monID = str(monID[0][0])
    except Exception:
        if monID == []:
            monID = performSQL("""SELECT DISTINCT pn.pokemonid FROM pokemon.pokemonnickname pn
                                WHERE pn.pokemonnickname = '"""+monName+"'")
            monID = str(monID[0][0])
            monName = performSQL("""SELECT DISTINCT mon.pokemonname FROM pokemon.pokemon mon
                                WHERE mon.pokemonid = """+monID)
            monName = str(monName[0][0])
        else:
            traceback.print_exc()
    return monID

def getMonInfo(monName,channel):
    monID = getMonID(monName)
    monName = monName.title()
    game = getGame(channel)
    availability = performSQL("""SELECT DISTINCT pa.pokemonavailabilitytypeid
                                FROM pokemon.pokemongameavailability pa
                                LEFT JOIN pokemon.game ga ON pa.gameid = ga.gameid
                                LEFT JOIN pokemon.gamegroup gg ON gg.gamegroupid = ga.gamegroupid
                                WHERE pa.pokemonid = """+monID+" AND gg.gamegroupabbreviation = '"+game+"'")
    if availability[0][0] == 18:
        message = monName + " is not available in " + game + "."
        return message
    #this section gets all the info to be compiled in a string at the end of this function
    #this is needed to fix the spelling of the pokemon name
    monName = performSQL("""SELECT DISTINCT mon.pokemonname FROM pokemon.pokemon mon WHERE pokemonid = """+monID)[0][0]
    monDex = getMonDex(monID, channel)
    monTypes = getMonTypes(monID, channel)
    monBST = getMonBST(monID, channel)
    monCaptureRate = getCaptureRate(monID, channel)
    monXPYield = getXPYield(monID, channel)
    monEvos = getMonEvos(monID, channel)
    monMoves = getMonMoves(monID, channel)
    #compiling all of the bits of info into one long string for return
    monInfo = "#" + monDex +" " + monName + " ("+game+") " + monTypes + " | Catch: "+monCaptureRate+"% | BST: " + monBST + " | XP: " + monXPYield + " | " + monEvos + " | " + monMoves
    return monInfo

def getGeneration(channel):
    config = configparser.ConfigParser()
    file = "../chatbot.ini"
    config.read(file)
    generation = config[channel]["generation"]
    return generation

def getMonDex(monID, channel):
    sql = """SELECT DISTINCT mon.pokemonpokedexnumber FROM pokemon.pokemon mon"""
    sql += " WHERE mon.pokemonid = "+monID
    dexArray = performSQL(sql)
    monDex = str(dexArray[0][0])
    return monDex

def getMonTypes(monID, channel):
    gen = getGeneration(channel)
    sql = """SELECT DISTINCT ty.typename, pt.generationid gen
            FROM pokemon.pokemontype pt
            LEFT JOIN pokemon.type ty ON pt.typeid = ty.typeid """
    sql += "WHERE pt.pokemonid = "+monID
    sql += " AND pt.generationid <= "+gen+" ORDER BY gen DESC LIMIT 2"
    typeArray = performSQL(sql)
    #if there are two types, store as (Type1/Type2)
    print(str(typeArray))
    types = "("+str(typeArray[0][0])
    if len(typeArray) > 1:
        types += "/"+str(typeArray[1][0])+")"
    #otherwise, store as (Type)
    else:
        types += ")"
    return types

def getMonBST(monID, channel):
    gen = getGeneration(channel)
    sql = """SELECT SUM(ps.pokemonstatvalue) bst, ps.generationid gen
            FROM pokemon.pokemonstat ps """
    sql += "LEFT JOIN pokemon.pokemon mon ON ps.pokemonid = mon.pokemonid WHERE mon.pokemonid ="+monID
    sql += " AND ps.generationid <= "+gen+" GROUP BY gen ORDER BY gen DESC LIMIT 1"
    bstArray = performSQL(sql)
    monBST = str(bstArray[0][0])
    return monBST

def getCaptureRate(monID, channel):
    sql = "SELECT DISTINCT mon.pokemoncapturerate FROM pokemon.pokemon mon "
    sql += "WHERE mon.pokemonid = """+monID+" LIMIT 1"
    captureRate = performSQL(sql)
    try:
        captureRate = captureRate[0][0]
        captureRate = 0.0000000000566758779982193 * math.pow(captureRate,5) - 0.0000000427601042779669*math.pow(captureRate,4) + 0.0000125235963016363*math.pow(captureRate,3) - 0.00191121035271638*math.pow(captureRate,2) + 0.311407303213974*captureRate + 0.846589688792571
        captureRate = round(captureRate, 2)
        captureRate = str(captureRate)
    except:
        print("Did not retrieve capture rate correctly.")
        captureRate = "#"
    return captureRate

def getXPYield(monID, channel):
    gen = getGeneration(channel)
    sql = "SELECT DISTINCT xp.experienceyieldvalue,xp.generationid gen FROM pokemon.pokemonexperienceyield xp "
    sql += "WHERE xp.pokemonid = "+monID+" "
    sql += "AND xp.generationid <= "+gen+" ORDER BY gen DESC LIMIT 1"
    xpYieldArray = performSQL(sql)
    try:
        xp=str(xpYieldArray[0][0])
    except:
        xp="unknown"
    return xp

def getMonEvos(monID, channel):
    gen = getGeneration(channel)
    sql = "SELECT DISTINCT mon.pokemonname"
    sql += """, pel.pokemonevolutionlevel,
            i.itemname, l.locationname, pe.evolutiontypeid, pes.pokemonevolutionuniquestring, m.movename, gg.generationid
            FROM pokemon.pokemonevolution pe """
    sql += """LEFT JOIN pokemon.pokemon mon ON pe.targetpokemonid = mon.pokemonid """
    sql +="""LEFT JOIN pokemon.pokemonevolutionlevel pel ON pe.pokemonevolutionid = pel.pokemonevolutionid
            LEFT JOIN pokemon.pokemonevolutionmove pem ON pe.pokemonevolutionid = pem.pokemonevolutionid
            LEFT JOIN pokemon.move m ON pem.moveid = m.moveid
            LEFT JOIN pokemon.pokemonevolutionitem pei ON pe.pokemonevolutionid = pei.pokemonevolutionid
            LEFT JOIN pokemon.item i ON pei.itemid = i.itemid
            LEFT JOIN pokemon.pokemonevolutionlocation ploc ON pe.pokemonevolutionid = ploc.pokemonevolutionid
            LEFT JOIN pokemon.location l ON ploc.locationid = l.locationid
            LEFT JOIN pokemon.gamegroup gg ON pe.gamegroupid = gg.gamegroupid
            LEFT JOIN pokemon.pokemonevolutionstring pes ON pe.pokemonevolutionid = pes.pokemonevolutionid"""
    sql += " WHERE pe.basepokemonid = "+monID+" "
    sql += """ AND gg.generationid <="""+gen+""" ORDER BY generationid ASC LIMIT 1"""
    evoArray = performSQL(sql)
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

def getMonMoves(monID, channel):
    game = getGame(channel)
    sql = """SELECT DISTINCT mv.movename,pm.pokemonmovelevel FROM pokemon.pokemonmove pm 
            LEFT JOIN pokemon.move mv ON pm.moveid = mv.moveid
            LEFT JOIN pokemon.generationmove gm ON mv.moveid = gm.moveid
            LEFT JOIN pokemon.gamegroup gg ON pm.gamegroupid = gg.gamegroupid """
    sql += "WHERE pm.pokemonid ="+monID
    sql+=" AND pokemonmovelevel > 1 AND gg.gamegroupabbreviation ='"+game+"' ORDER BY pm.pokemonmovelevel ASC"
    movesArray = performSQL(sql)
    if movesArray == []:
        moveList = "Does not learn moves"
    else:
        moveList = "Learns moves at "
        for move in movesArray:
            moveList += str(move[1])+", "
            #remove the extra comma and space after
        moveList = moveList[0:len(moveList)-2]
    return moveList

def getMoveInfo(moveName, channel):
    gen = getGeneration(channel)
    moveName = moveName.title()
    try:
        moveID = getMoveID(moveName)
        moveList = performSQL("""SELECT m.movename, t.typename, mc.movecategoryname, gm.movecontactflag,
                            gm.movepp, gm.movepower, gm.moveaccuracy, gm.movepriority, gm.movedescription, gm.generationid
                            FROM pokemon.generationmove as gm
                            LEFT JOIN pokemon.move as m ON gm.moveid = m.moveid
                            LEFT JOIN pokemon.type AS t ON gm.typeid = t.typeid
                            LEFT JOIN pokemon.movecategory AS mc ON gm.movecategoryid = mc.movecategoryid
                            WHERE gm.moveid = '""" + moveID + "' AND gm.generationid = " + gen)
        moveList=moveList[0]
        if 'True' in str(moveList[3]):
            moveContact = "C"
        else:
            moveContact = "NC"
        info = str(moveList[0])+" - Gen " +gen+ ": ("+str(moveList[1])+", "+str(moveList[2])+", "+moveContact+") | PP: "+str(moveList[4])+" | Power: "+str(moveList[5])+" | Acc.: "+str(moveList[6])+" | Priority: "+str(moveList[7])+" | Summary: "+str(moveList[8])
    except Exception:
        traceback.print_exc()
        info = 'I could not find "' +moveName+'" in generation '+gen+'. Note that I prefer "Bubble Beam," not "BubbleBeam".'
    return info

def getAbilityInfo(abilityName, channel):
    gen = getGeneration(channel)
    abilityName = abilityName.title()
    allowedAbilities = str(performSQL("SELECT ability.abilityname FROM pokemon.ability"))
    if abilityName in allowedAbilities:
        abilityTuple = performSQL("""SELECT ga.abilitydescription FROM pokemon.generationability ga
                                    LEFT JOIN pokemon.ability ab ON ga.abilityid = ab.abilityid
                                    WHERE ab.abilityname = '"""+abilityName+"' AND ga.generationid <= """
                                    +gen+" ORDER BY ga.generationid DESC LIMIT 1")
        if not abilityTuple == []:
            abilitySum = str(abilityTuple[0][0])
            print(abilitySum)
            abilityInfo = abilityName + " (Gen "+gen+"): " + abilitySum
        else:
            abilityInfo = "Could not find info for ability '"+abilityName+"' in generation " + gen + "."
    else:
        abilityInfo = "Could not find info for ability '"+abilityName+"' in generation " + gen + "."
    return abilityInfo

def getNatureInfo(natureName):
    natureName = natureName.title()
    allowedNatures = str(performSQL("SELECT nature.naturename from pokemon.nature"))
    if natureName in allowedNatures:
        neutral = performSQL("SELECT n.neutralnatureflag FROM pokemon.nature n WHERE n.naturename = '"+natureName+"'")
        if 'True' in str(neutral):
            natureInfo  = natureName + " is a neutral nature."
        elif 'False' in str(neutral):
            raisedStat  = performSQL("SELECT s.statname FROM pokemon.nature n LEFT JOIN pokemon.stat s ON n.raisedstatid = s.statid WHERE n.naturename = '"+natureName+"'")
            loweredStat = performSQL("SELECT s.statname FROM pokemon.nature n LEFT JOIN pokemon.stat s ON n.loweredstatid = s.statid WHERE n.naturename = '"+natureName+"'")
            natureInfo  = "+"+str(raisedStat[0][0])+"/"+"-"+str(loweredStat[0][0])
    else:
        natureInfo = "Could not find info for "+natureName+"."
    return natureInfo

def getWeaknessInfo(monName, channel):
    try:
        monID = getMonID(monName)
        gen = getGeneration(channel)
        matchupInfo = performSQL("""SELECT DISTINCT attackType.typename,defendType.typename,tm.damagemodifier::float,tm.generationid
                                    FROM pokemon.pokemontype pt
                                    LEFT JOIN pokemon.typematchup tm ON pt.typeid = tm.defendingtypeid
                                    LEFT JOIN pokemon.type attackType ON tm.attackingtypeid = attackType.typeid
                                    LEFT JOIN pokemon.type defendType ON tm.defendingtypeid = defendType.typeid
                                    WHERE pt.pokemonid ="""+monID+""" 
                                    AND pt.generationid <="""+gen+""" 
                                    AND tm.generationid <="""+gen+""" 
                                    GROUP BY attackType.typename,defendType.typename,tm.damagemodifier,tm.generationid
                                    ORDER BY attackType.typename,defendType.typename,tm.generationid""")
        print(str(matchupInfo))
        effectivenessDict = {}
        for matchup in matchupInfo:
            effectivenessDict[matchup[0]] = 1
        for matchup in matchupInfo:
            if (matchup[0] == 'Dark' or matchup[0] == 'Ghost') and matchup[1] == 'Steel' and int(gen) > 5 and matchup[3]==2:
                pass
            else:
                effectivenessDict[matchup[0]] = effectivenessDict[matchup[0]]*matchup[2]
        printableDict = {4.0:[],2.0:[],1.0:[],.5:[],.25:[],0:[]}
        for type,dmgmodifier in effectivenessDict.items():
            printableDict[dmgmodifier].append(type)
        monTypes = getMonTypes(monID, channel)
        weaknessInfo = monName.title() +" "+ monTypes + ", Gen " +gen+" = \r"
        if printableDict[4.0]:
            weaknessInfo += "(4x): " + str(printableDict[4.0])+ " // "
        if printableDict[2.0]:
            weaknessInfo += "(2x): " + str(printableDict[2.0]) + " // "
        if printableDict[1.0]:
            weaknessInfo += "(1x): " + str(printableDict[1.0]) + " // "
        if printableDict[0.5]:
            weaknessInfo += "(.5x): " + str(printableDict[0.5]) + " // "
        if printableDict[0.25]:
            weaknessInfo += "(.25x): " + str(printableDict[0.25]) + " // "
        if printableDict[0]:
            weaknessInfo += "0x: " + str(printableDict[0])
    except Exception:
        traceback.print_exc()
        weaknessInfo = "Unable to retrieve effectiveness info for pokemon "+monName.title()+" in generation "+gen+"."
        
    weaknessInfo = weaknessInfo.replace('[','').replace(']','').replace("\'","")
    return weaknessInfo

def getCoverage(types):
    pass

def dbConfig(configFile = "../chatbot.ini",section="database"):
    config = configparser.ConfigParser()
    config.read(configFile)
    db = {}
    if config.has_section(section):
        configuration = config.items(section)
        for option in configuration:
            db[option[0]] = option[1]
    else:
        raise Exception("Could not find section "+section+" in config file "+configFile)
    return db

def chatMessage(messageString, channel, server):
    server.send(bytes('PRIVMSG #'+ channel + ' :'+messageString+' \r\n', 'utf-8'))

def performSQL(sql):
    dbConn = dbConfig()
    print("Connecting to database...")
    conn = psycopg2.connect(**dbConn)
    with conn.cursor() as cur:
        print("Executing " +sql)
        cur.execute(sql)
        result = cur.fetchall()
    return result

def setGame(gameAbbr, channel, server):
    if len(gameAbbr) > 1:
        chatMessage("Too many parameters for !game command.", channel, server)
    elif len(gameAbbr) < 1:
        chatMessage("Command !game requires a game abbreviation as a parameter (RB, Y, GS, C, FRLG, HGSS, DP, etc.).", channel, server)
    else:
        gameAbbr = gameAbbr[0]
        try:
            game = gameAbbr.upper()
            config = configparser.ConfigParser()
            allowedGames = performSQL("SELECT gg.gamegroupabbreviation FROM pokemon.gamegroup gg")
            if game in str(allowedGames):
                generation = performSQL("SELECT gg.generationid FROM pokemon.gamegroup gg WHERE gg.gamegroupabbreviation = '"+game+"'")
                generation = str(generation[0][0])
                file = "../chatbot.ini"
                config.read(file)
                operators = config[channel]['operators']
                config[channel] = {
                    "generation": generation,
                    "game": game,
                    "operators": operators
                }
                with open(file, 'w+') as configfile:
                    config.write(configfile)
                success = "Successfully changed the game to "+game+"."
            else:
                success = game+" is not a valid abbreviation. Valid abbreviations are "+str(allowedGames)+"."
        except:
            success = "I wasn't able to change the game to "+game+"."
        return success

def getGame(channel):
    config = configparser.ConfigParser()
    file = "../chatbot.ini"
    config.read(file)
    game = config[channel]["game"]
    return game

if __name__ == "__main__":
    main()