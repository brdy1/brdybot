#this is for opening the configuration file
import sys
import configparser
#this is for connecting to IRC
import socket
#this is for connecting to the postgres database
import psycopg2
#this is for doing cute equations
import math
#for multithreading for additional channels
import threading
#traceback is for error handling/printing so i can figure out what went wrong
import traceback
#sleep is so the bot won't overload during listening
from time import sleep

def main():
    conn, token, user, readbuffer, server = connectionVariables()
    #channels = performSQL("SELECT channelname FROM bot.channel ch WHERE ch.channelname = 'brdy'")
    channels = performSQL("SELECT channelname FROM bot.channel ch WHERE ch.channelid NOT in(SELECT cd.channelid FROM bot.channeldeletion cd)")
    commandDict = getCommands()
    for channel in channels:
        channel = channel[0]
        operators = getOperants(channel)
        threading.Thread(target=ircListen, args=(conn, token, user, channel, server, operators, commandDict)).start()
        sleep(2)

def getOperants(channel):
    operators = []
    operants = performSQL("""SELECT operantname FROM bot.channeloperant co
                                    LEFT JOIN bot.channel ch ON co.channelid = ch.channelid
                                    LEFT JOIN bot.operant op ON co.operantid = op.operantid
                                    WHERE ch.channelname = '"""+channel+"'")
    for operant in operants:
        operators.append(operant[0])
    return operators

def connectionVariables():
    connection_data = ('irc.chat.twitch.tv', 6667)
    token = getToken()
    botName = "brdybot"
    readbuffer = ''
    server = socket.socket()
    return connection_data, token, botName, readbuffer, server

def getToken():
    config = configparser.ConfigParser()
    file = "chatbot.ini"
    config.read(file)
    token = config['chatbot']['token']
    return token

def ircListen(conn, token, botName, channel, server, operators, commandDict):
    try:
        listenFlag = True
        #joining the channel
        server = socket.socket()
        server.connect(conn)
        server.send(bytes('PASS ' + token + '\r\n', 'utf-8'))
        server.send(bytes('NICK ' + botName + '\r\n', 'utf-8'))
        server.send(bytes('JOIN #' + channel + '\r\n', 'utf-8'))
        #listening loop
        print("Starting bot in channel " +channel + " with operants: "+str(operators))
        while listenFlag:
            response = server.recv(2048).decode('utf-8')
            if len(response) == 0:
                break
            if "PING" in str(response):
                pong = str(response).replace("PING","PONG")
                server.send(bytes(pong, 'utf-8'))
                server.send(bytes('PONG\r\n', 'utf-8'))
            elif "!" in str(response):
                #fetch the username,message,etc. from the response without grabbing pings, errors, or erroneous messages
                if len(str(response)) > 2:
                    username = str(response).split('!',1)[0][1:]
                    if ":" in str(response):
                        splitResp = str(response).split(':')
                        if len(splitResp) > 3:
                            splitResp = str(response).split(':')[2]+str(response).split(':')[3]
                        else:
                            splitResp = str(response).split(':')[2]
                        userMessage = splitResp[0:len(splitResp)-2]
                else:
                    userMessage = " "
                command = userMessage.split(" ")[0].lower().replace("'","''")
                parameters = userMessage.split(" ")[1:]
                permissions = (username in operators) or (channel == 'brdybot') or (command == "!botinfo")
                if ("!" in command[0:1]) and (command[1:] in commandDict) and permissions:
                    commandid = commandDict[command[1:]]
                    commandrequestid = logCommand(commandid,channel,username,parameters)
                    message = None
                    message = doCommand(commandrequestid)
                    if message:
                        chatMessage(message,channel,server)
                        operators = getOperants(channel)
                        success = storeMessage(message, commandrequestid)
            sleep(1)
    except ConnectionResetError:
        logException(None, "ConnectionResetError", channel)
    except IndexError:
        logException(commandrequestid,"IndexError", channel)
    except KeyError:
        logException(commandrequestid,"KeyError", channel)
    except RuntimeError:
        logException(commandrequestid,"RuntimeError", channel)
    except SystemExit:
        logException(commandrequestid,"SystemExit", channel)
    except ValueError:
        logException(commandrequestid,"ValueError", channel)
    except BrokenPipeError:
        logException(commandrequestid,"BrokenPipeError", channel)
    except ConnectionAbortedError:
        logException(commandrequestid,"ConnectionAbortedError", channel)
    except ConnectionRefusedError:
        logException(commandrequestid,"ConnectionRefusedError", channel)
    except FileNotFoundError:
        logException(commandrequestid,"FileNotFoundError", channel)
    except TimeoutError:
        logException(commandrequestid,"TimeoutError", channel)
    except Exception:
        logException(commandrequestid,"OtherError", channel)

def getCommands():
    commands = performSQL("SELECT commandid,commandname FROM bot.command")
    commandDict = {}
    for command in commands:
        commandDict[command[1]] = command[0]
    return commandDict

def doCommand(commandrequestid):
    conn, token, botName, readbuffer, server = connectionVariables()
    parameters = []
    ccr = performSQL("SELECT com.commandname,ch.channelname,op.operantname,ccrp.channelcommandrequestparameter FROM bot.channelcommandrequest ccr LEFT JOIN bot.command com ON ccr.commandid = com.commandid LEFT JOIN bot.channel ch ON ccr.channelid = ch.channelid LEFT JOIN bot.operant op ON ccr.operantid = op.operantid LEFT JOIN bot.channelcommandrequestparameter ccrp ON ccr.channelcommandrequestid = ccrp.channelcommandrequestid WHERE ccr.channelcommandrequestid ="+str(commandrequestid))
    for command,channel,username,parameter in ccr:
        parameters.append(parameter)
    if command == "mon":
        message = getMonInfo(parameters,channel)
    elif command == "move":
        message = getMoveInfo(parameters,channel)
    elif command == "ability":
        message = getAbilityInfo(parameters,channel)
    # elif command == "xp":
    #     message = getXPYield()
    # elif command == "bst":
    #     message = getBST()
    # elif command == "learnset":
    #     message = getMonMoves()
    # elif command == "evolution":
    #     message = getMonEvo()
    elif command == "nature":
        message = getNatureInfo(parameters,channel)
    elif command == "weak":
        message = getWeaknessInfo(parameters,channel)
    elif command == "coverage":
        message = getCoverage(parameters,channel)
    elif command == "abbrevs":
        message = getAbbrevs()
    elif command == "gamelist":
        message = getGames()
    elif command == "pokegame":
        message = setGame(parameters, channel, server)
    elif command == "pokeops":
        message = addOperants(parameters,channel)
    elif command == "removeops" and channel == username:
        message = removeOperants(parameters,channel)
    elif command == "listops":
        message = listOperants(channel)
    elif command == "join" and channel == "brdybot":
        message = addClient(conn,token,botName,username,server)
    elif command == "brdybotleave" and channel == username:
        message = removeClient(username)
    elif command == "pokecom":
        commands = "!mon, !move, !ability, !coverage, !nature, !weak, !pokegame, !abbrevs, !gamelist, !botinfo, !listops, !pokeops, !pokecom, !brdybotleave"
        message = "Available commands are " + commands + "."
    elif command == "botinfo":
        message = "Visit https://www.twitch.tv/brdybot/about"
    return message

def storeMessage(message,ccrid):
    success = performSQL("UPDATE bot.channelcommandrequest SET channelcommandrequestreturn ='"+message.replace("'","''")+"' WHERE channelcommandrequestid = "+str(ccrid)+" RETURNING channelcommandrequestid;")
    return success

def logException(commandrequestid, exception, channel):
    channelid = getChannelID(channel)
    if not commandrequestid:
        commandrequestid = "null"
    errortypeid = performSQL("SELECT errortypeid FROM bot.errortype WHERE errortypename = '"+exception+"'")
    if errortypeid != []:
        errortypeid = errortypeid[0][0]
    else:
        errortypeid = performSQL("SELECT errortypeid FROM bot.errortype WHERE errortypename = 'OtherError'")
    channelerrorid = performSQL("INSERT INTO bot.channelerror (channelcommandrequestid,errortypeid) VALUES ("+str(commandrequestid)+","+str(errortypeid)+") RETURNING channelerrorid;")
    traceback.print_exc()
    print(" with channelerrorid = "+str(channelerrorid))
    commandDict = getCommands()
    conn, token, user, readbuffer, server = connectionVariables()
    operators = getOperants(channel) 
    threading.Thread(target=ircListen, args=(conn, token, "brdybot", channel, server, operators, commandDict)).start()
    sys.exit()

def getChannelID(channel):
    channelid = performSQL("SELECT ch.channelid FROM bot.channel ch WHERE ch.channelname ='"+channel+"'")[0][0]
    return channelid

def logCommand(commandid,channelname,operantname,parameters):
    commandname = performSQL("SELECT com.commandname FROM bot.command com WHERE com.commandid = "+str(commandid))[0][0]
    if commandid == 9:
        success = addOperants([operantname],channelname)
    channelid = getChannelID(channelname)
    operantid = performSQL("SELECT op.operantid FROM bot.operant op WHERE op.operantname = '"+operantname+"'")[0][0]
    print("\r\n________________________________________________________________________________________________________")
    print("Received the "+commandname+" command in channel "+channelname+" from user "+operantname+". Parameters: "+str(parameters)+"\r\n")
    channelcommandrequestid = performSQL("INSERT INTO bot.channelcommandrequest (commandid,channelid,operantid) VALUES ("+str(commandid)+","+str(channelid)+","+str(operantid)+") RETURNING channelcommandrequestid;")[0][0]
    for parameter in parameters:
        parameter = parameter.replace("'","''")
        parameterid = performSQL("INSERT INTO bot.channelcommandrequestparameter (channelcommandrequestid,channelcommandrequestparameter) VALUES ("+str(channelcommandrequestid)+",'"+parameter+"') RETURNING channelcommandrequestparameterid;")
    return channelcommandrequestid

def addOperants(parameters, channel):
    note = " User(s) "
    exists = False
    for parameter in parameters:
        parameter = parameter.lower()
        operantid = performSQL("SELECT operantid FROM bot.operant WHERE operantname = '"+parameter+"'")
        if operantid == []:
            operantid = performSQL("INSERT INTO bot.operant (operantname) values ('"+parameter+"') RETURNING operantid;")[0][0]
        else:
            operantid = operantid[0][0]
        operantid = str(operantid)
        channeloperantid = performSQL("SELECT channeloperantid FROM bot.channeloperant co LEFT JOIN bot.channel ch ON co.channelid = ch.channelid LEFT JOIN bot.operant op ON co.operantid = op.operantid WHERE ch.channelname = '"+channel+"' AND co.operantid ="+operantid)
        if channeloperantid == []:
            sql = "INSERT INTO bot.channeloperant (channelid,operantid,operanttypeid) VALUES ((SELECT channelid FROM bot.channel WHERE channelname ='"+channel+"'),"+operantid+",2) RETURNING channeloperantid;"
            channeloperantid = performSQL(sql)
        else:
            exists = True
            if parameters.index(parameter) < len(parameters)-3:
                note += parameter + ", "
            elif parameters.index(parameter) < len(parameters)-2:
                note += parameter + " and "
            elif parameters.index(parameter) < len(parameters)-1:
                note += parameter + " "
    message = "Successfully added bot users to configuration."
    if exists:
        message += note + " already exist(s) as bot user(s) in channel "+channel+"."
    return message

def removeOperants(parameters, channel):
    message = "User(s) "
    for parameter in parameters:
        parameter = parameter.lower()
        if parameter != channel:
            sql = """DELETE FROM bot.channeloperant
                    WHERE channeloperantid =
                    (SELECT channeloperantid
                    FROM bot.channeloperant co
                    INNER JOIN bot.channel ch ON co.channelid = ch.channelid
                    INNER JOIN bot.operant op ON co.operantid = op.operantid
                    WHERE ch.channelname = '"""+channel+"' AND op.operantname = '"+parameter+"""')
                    RETURNING operantid;"""
            operantid = performSQL(sql)
            message += parameter
        else:
            message = "You cannot remove the channel owner from the operant list. "+message
    message += " were removed from the channel's user list."
    return message

def listOperants(channel):
    message = "Users who have permissions in channel "+channel+": "
    operants = getOperants(channel)
    for operant in operants:
        if operants.index(operant) < len(operants)-1:
            message += operant+", "
        else:
            message += operant
    return message

def addClient(conn, token, botName, username, server):
    channelid = performSQL("SELECT channelid FROM bot.channel WHERE channelname = '"+username+"'")
    operantid = performSQL("SELECT operantid FROM bot.operant WHERE operantname = '"+username+"'")
    if channelid == []:
        sql = "INSERT INTO bot.channel (channelname,gameid) VALUES ('"+username+"',10) RETURNING channelid;"
        channelid = performSQL(sql)
    if operantid == []:
        sql = "INSERT INTO bot.operant (operantname) VALUES ('"+username+"') RETURNING operantid;"
        operantid = performSQL(sql)
    sql = """SELECT operanttypeid FROM bot.channeloperant co
                LEFT JOIN bot.channel ch ON co.channelid = ch.channelid
                LEFT JOIN bot.operant op ON co.operantid = op.operantid
                WHERE ch.channelname = '"""+username+"""' AND op.operantname ='"""+username+"'"
    channeloperantid = performSQL(sql)
    if channeloperantid == []:
        sql = "INSERT INTO bot.channeloperant (channelid, operantid, operanttypeid) VALUES ("+str(channelid[0][0])+","+str(operantid[0][0])+",1) RETURNING channeloperantid;"
        channeloperantid = performSQL(sql)
        message = username+""" - You have been successfully added to the channel list.
                                Game has been set to FireRed. Use !pokegame in your channel to change the game.
                                Note that I do store usernames and command usage records in the database for use in feature improvement.
                                Your username will NEVER be shared with anyone for any reason.
                                Use !brdybotleave in your channel to remove yourself from my channel list."""
        operants = getOperants(username)
        commandDict = getCommands()
        threading.Thread(target=ircListen, args=(conn, token, botName, username, server, operants,commandDict)).start()
    elif channeloperantid[0][0] == 1:
        message = username+" - I should be operating in your channel. If I'm not, message brdy on Discord to correct the error."
    return message

def removeClient(channel):
    sql = "INSERT INTO  bot.channeldeletion (channelid) values (SELECT ch.channelid FROM bot.channel ch WHERE ch.channelname = '"+channel+"') RETURNING channelid"
    channelid = performSQL(sql)
    message = channel+" - Successfully removed you from the channel list."
    return message

def getMoveID(moveName):
    moveID = performSQL(""" WITH ldist as (SELECT mv.moveid,LEAST(pokemon.levenshtein(mv.movename, '"""+moveName+"""'),
                            pokemon.levenshtein(mn.movenickname, '"""+moveName+"""')) AS distance FROM pokemon.move mv
                            LEFT JOIN pokemon.movenickname mn ON mv.moveid = mn.moveid)
                            SELECT moveid,distance FROM ldist WHERE distance < 5 ORDER BY distance LIMIT 1""")
    moveID = str(moveID[0][0])
    return moveID

def combineParameters(parameters):
    name = ""
    for parameter in parameters:
        name += parameter + " "
    name = name[:len(name)-1].title()
    return name

def getMonID(monName,channel):
    monName = monName.replace("'","''")
    monID = performSQL("""WITH ldist as (SELECT DISTINCT mon.pokemonid,LEAST(pokemon.levenshtein(mon.pokemonname,'"""+monName+"""'),
                            pokemon.levenshtein(pn.pokemonnickname,'"""+monName+"""')) AS distance FROM pokemon.pokemon mon 
                            LEFT JOIN pokemon.pokemonnickname pn ON mon.pokemonid = pn.pokemonid) 
                            SELECT pokemonid,distance FROM ldist WHERE distance < 5 ORDER BY distance LIMIT 1""")
    if monID == []:
        errorString = "Could not find Pokemon "+monName+"."
        return None,errorString
    monID = str(monID[0][0])
    monName = performSQL("""SELECT DISTINCT mon.pokemonname FROM pokemon.pokemon mon
                            WHERE mon.pokemonid = """+monID)
    monName = str(monName[0][0])
    return monID,monName

def getMonInfo(parameters,channel):
    if len(parameters) < 1:
        monInfo = "The !mon command requires the name of a pokemon as a parameter. (ex: '!mon charizard')"
        return monInfo
    monName = combineParameters(parameters)
    monID,monName = getMonID(monName,channel)
    game = getGame(channel)
    if monID == None:
        return monName
    availability = performSQL("""SELECT DISTINCT pa.pokemonavailabilitytypeid
                                FROM pokemon.pokemongameavailability pa
                                LEFT JOIN pokemon.game ga ON pa.gameid = ga.gameid
                                LEFT JOIN pokemon.gamegroup gg ON gg.gamegroupid = ga.gamegroupid
                                WHERE pa.pokemonid = """+monID+" AND gg.gamegroupabbreviation = '"+game+"'")
    if availability[0][0] == 18:
        message = monName + " is not available in " + game + "."
        return message
    #this section gets all the info to be compiled in a string at the end of this function
    monName,monDex,monGrowth,monCaptureRate = performSQL("""SELECT DISTINCT mon.pokemonname,mon.pokemonpokedexnumber,
                            lr.levelingratename,mon.pokemoncapturerate 
                            FROM pokemon.pokemon mon 
                            LEFT JOIN pokemon.levelingrate lr ON mon.levelingrateid = lr.levelingrateid 
                            WHERE pokemonid = """+monID)[0]
    monDex = str(monDex)
    monCaptureRate = getCaptureRate(monCaptureRate, channel)
    monTypes = getMonTypes(monID, channel)
    monBST = getMonBST(monID, channel)
    monXPYield = getXPYield(monID, channel,5,5)
    monEvos = getMonEvos(monID, channel)
    monMoves = getMonMoves(monID, channel)
    #compiling all of the bits of info into one long string for return
    monInfo = "#" + monDex +" " + monName + " ("+game+") " + monTypes + " | Catch: "+monCaptureRate+"% | BST: " + monBST + " | L5 XP: " + monXPYield + " | " + monGrowth + " | " + monEvos + " | " + monMoves
    return monInfo

def getMonGrowth(monID,channel):
    sql = "SELECT lr.levelingratename FROM pokemon.levelingrate lr LEFT JOIN pokemon.pokemon mon ON lr.levelingrateid = mon.levelingrateid WHERE mon.pokemonid = "+monID
    rate = str(performSQL(sql)[0][0])
    return rate

def getGeneration(channel):
    generation = performSQL("""SELECT gen.generationid FROM bot.channel ch
                               LEFT JOIN pokemon.game gm ON ch.gameid = gm.gameid
                               LEFT JOIN pokemon.gamegroup gg ON gm.gamegroupid = gg.gamegroupid
                               LEFT JOIN pokemon.generation gen ON gg.generationid = gen.generationid
                               WHERE ch.channelname = '"""+channel+"'")[0][0]
    generation = str(generation)
    return generation

def getMonDex(monID, channel):
    sql = """SELECT DISTINCT mon.pokemonpokedexnumber FROM pokemon.pokemon mon"""
    sql += " WHERE mon.pokemonid = "+monID
    dexArray = performSQL(sql)
    monDex = str(dexArray[0][0])
    return monDex

def getMonTypes(monID, channel):
    
    gen = getGeneration(channel)
    monTypes = """WITH monTypes as (SELECT pokemonid,type1id,type2id
                    FROM pokemon.crosstab('select pokemonid, typeid as type1id, typeid as type2id
                FROM pokemon.pokemontype pt WHERE pt.generationid = """+gen+"""
                AND pt.pokemonid = """+monID+"""
                GROUP BY pokemonid,type1id,type2id ORDER BY pokemonid,type1id,type2id')
                        AS ct( pokemonid int, type1id int, type2id int)) \r\n"""
    mainSelect = """SELECT type1.typename,type2.typename FROM monTypes
                    LEFT JOIN pokemon.type type1 ON monTypes.type1id = type1.typeid
                    LEFT JOIN pokemon.type type2 ON monTypes.type2id = type2.typeid"""
    typeArray = performSQL(monTypes+mainSelect)
    #if there are two types, store as (Type1/Type2)
    #print(str(typeArray))
    types = "("+str(typeArray[0][0])
    if typeArray[0][1] != None:
        types += "/"+str(typeArray[0][1])+")"
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

def getCaptureRate(captureRate,channel):
    #this formula approximates the catch rate to within about .1% and will work for future catch rates not currently being used
    captureRate = 0.0000000000566758779982193 * math.pow(captureRate,5) - 0.0000000427601042779669*math.pow(captureRate,4) + 0.0000125235963016363*math.pow(captureRate,3) - 0.00191121035271638*math.pow(captureRate,2) + 0.311407303213974*captureRate + 0.846589688792571
    captureRate = round(captureRate, 1)
    captureRate = str(captureRate)
    return captureRate

def getXPYield(monID, channel,enemylevel,monlevel):
    gen = getGeneration(channel)
    sql = "SELECT DISTINCT xp.experienceyieldvalue,xp.generationid gen FROM pokemon.pokemonexperienceyield xp "
    sql += "WHERE xp.pokemonid = "+monID+" "
    sql += "AND xp.generationid <= "+gen+" ORDER BY gen DESC LIMIT 1"
    xpYieldArray = performSQL(sql)
    if xpYieldArray == []:
        xp="unknown"
    else:
        gen = int(gen)
        monyield = xpYieldArray[0][0]
        xp = monyield*enemylevel/7
        xp=str(int(round(xp,0)))
    return xp

def getMonEvos(monID, channel):
    gen = getGeneration(channel)
    sql = "SELECT DISTINCT mon.pokemonname"
    sql += """, pel.pokemonevolutionlevel,
            i.itemname, l.locationname, pet.evolutiontypeid, pes.pokemonevolutionuniquestring, m.movename, gg.generationid
            FROM pokemon.pokemonevolution pe """
    sql += """LEFT JOIN pokemon.pokemon mon ON pe.targetpokemonid = mon.pokemonid """
    sql +="""LEFT JOIN pokemon.pokemonevolutionlevel pel ON pe.pokemonevolutionid = pel.pokemonevolutionid
            LEFT JOIN pokemon.pokemonevolutionmove pem ON pe.pokemonevolutionid = pem.pokemonevolutionid
            LEFT JOIN pokemon.move m ON pem.moveid = m.moveid
            LEFT JOIN pokemon.pokemonevolutionitem pei ON pe.pokemonevolutionid = pei.pokemonevolutionid
            LEFT JOIN pokemon.item i ON pei.itemid = i.itemid
            LEFT JOIN pokemon.pokemonevolutionlocation ploc ON pe.pokemonevolutionid = ploc.pokemonevolutionid
            LEFT JOIN pokemon.location l ON ploc.locationid = l.locationid
            LEFT JOIN pokemon.pokemonevolutiontype pet ON pe.pokemonevolutionid = pet.pokemonevolutionid
            LEFT JOIN pokemon.gamegroup gg ON pe.gamegroupid = gg.gamegroupid
            LEFT JOIN pokemon.pokemonevolutionstring pes ON pe.pokemonevolutionid = pes.pokemonevolutionid"""
    sql += " WHERE pe.basepokemonid = "+monID+" "
    sql += """ AND gg.generationid = (SELECT MAX(gg.generationid) FROM pokemon.pokemonevolution pe
                                    LEFT JOIN pokemon.gamegroup gg ON pe.gamegroupid = gg.gamegroupid
                                    WHERE gg.generationid <="""+gen+""" AND pe.basepokemonid = """+monID+""")
                ORDER BY generationid DESC"""
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
            evoInfo += " as a female"
        elif evoType == 13:
            evoInfo += " as a male"
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
                evoInfo += " after being exposed to " + evoItem
            else:
                evoInfo += " while holding " + evoItem
        if not evoLocation == 'None':
            evoInfo += " at " + evoLocation
        if not evoMove == 'None':
            evoInfo += " while knowing " + evoMove
        if not evoUnique == 'None':
            evoInfo += " " + evoUnique
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

def getMoveInfo(parameters, channel):
    if len(parameters) < 1:
        info = 'The !move command requires the name of a move as a parameter.'
    else:
        moveName = combineParameters(parameters)
        moveName = moveName.replace("'","''")
        gen = getGeneration(channel)
        moveID = getMoveID(moveName)
        if moveID == []:
            info = 'I could not find a move called "' +moveName+'.'
        else:
            moveList = performSQL("""SELECT m.movename, t.typename, mc.movecategoryname, gm.movecontactflag,
                                gm.movepp, gm.movepower, gm.moveaccuracy, gm.movepriority, gm.movedescription, gm.generationid
                                FROM pokemon.generationmove as gm
                                LEFT JOIN pokemon.move as m ON gm.moveid = m.moveid
                                LEFT JOIN pokemon.type AS t ON gm.typeid = t.typeid
                                LEFT JOIN pokemon.movecategory AS mc ON gm.movecategoryid = mc.movecategoryid
                                WHERE gm.moveid = '""" + moveID + "' AND gm.generationid = " + gen)
            if moveList == []:
                info = 'I could not find a move called "' +moveName+'" in generation '+gen+'.'
            else:
                moveList=moveList[0]
                if 'True' in str(moveList[3]):
                    moveContact = "C"
                else:
                    moveContact = "NC"
                info = str(moveList[0])+" - Gen " +gen+ ": ("+str(moveList[1])+", "+str(moveList[2])+", "+moveContact+") | PP: "+str(moveList[4])+" | Power: "+str(moveList[5])+" | Acc.: "+str(moveList[6])+" | Priority: "+str(moveList[7])+" | Summary: "+str(moveList[8])
    return info

def getAbilityInfo(parameters, channel):
    if len(parameters) < 1:
        abilityInfo = "The !ability command requires the name of an ability as a parameter."
    else:
        abilityName = combineParameters(parameters)
        abilityName = abilityName.replace("'","''")
        gen = getGeneration(channel)
        abilityName = abilityName.title()
        abilityTuple = performSQL(""" WITH ldist as (SELECT ab.abilityname,ga.abilitydescription,ga.generationid,pokemon.levenshtein(ab.abilityname, '"""+abilityName+"""') AS distance FROM pokemon.generationability ga
                                        LEFT JOIN pokemon.ability ab ON ga.abilityid = ab.abilityid
                                        WHERE ga.generationid <= """+gen+""" )
                                        SELECT * FROM ldist 
                                        WHERE distance < 4 
                                        ORDER BY distance ASC LIMIT 1""")   
        if not abilityTuple == []:
            abilityName = str(abilityTuple[0][0])
            abilitySum = str(abilityTuple[0][1])
            print(abilitySum)
            abilityInfo = abilityName + " (Gen "+gen+"): " + abilitySum
        else:
            abilityInfo = "Could not find info for ability '"+abilityName+"' in generation " + gen + "."
    return abilityInfo

def getNatureInfo(parameters,channel):
    if len(parameters) < 1:
        natureInfo = "The !nature command requires the name of a nature as a parameter. (ex: !nature adamant)"
    else:
        natureName = combineParameters(parameters)
        natureList  = performSQL("""WITH ldist as (SELECT raisedstat.statname raisedstat,loweredstat.statname loweredstat,
                                                n.neutralnatureflag neutral,
                                                pokemon.levenshtein(n.naturename, '"""+natureName+"""') AS distance FROM pokemon.nature n
                                                LEFT JOIN pokemon.stat raisedstat ON n.raisedstatid = raisedstat.statid
                                                LEFT JOIN pokemon.stat loweredstat ON n.loweredstatid = loweredstat.statid)
                                                SELECT * FROM ldist WHERE distance < 5
                                                ORDER BY distance LIMIT 1""")
        if natureList == []:
            natureInfo = "Could not find info for "+natureName+"."
        else:
            raisedStat,loweredStat,neutral,distance = natureList[0]
            if 'True' in str(neutral):
                natureInfo  = natureName + " is a neutral nature."
            elif 'False' in str(neutral):
                natureInfo  = "+"+str(raisedStat)+"/"+"-"+str(loweredStat)
            else:
                natureInfo = "Could not find info for "+natureName+"."
    return natureInfo

def getWeaknessInfo(parameters, channel):
    if len(parameters) < 1:
        weaknessInfo = "The !weak command requires the name of a Pokemon as a parameter. (ex: !weak kartana)"
    else:
        monName = combineParameters(parameters)
        monID,monName = getMonID(monName,channel)
        if monID == None:
            return monName
        gen = getGeneration(channel)
        monTypes = """WITH montypes AS( SELECT pokemonid,type1id,type2id
                    FROM pokemon.crosstab('select pokemonid, typeid as type1id, typeid as type2id
                    FROM pokemon.pokemontype WHERE generationid = (SELECT MAX(generationid) FROM pokemon.pokemontype WHERE pokemonid = """+monID+""" AND generationid <= """+gen+""") AND pokemonid = """+monID+"""
                    GROUP BY pokemonid,type1id,type2id ORDER BY pokemonid,type1id,type2id')
                    AS ct( pokemonid int, type1id int, type2id int)), \r\n"""
        damage1 = """damage1 as (
                    SELECT DISTINCT attacktype.typename attacker,SUM(coalesce(tm.damagemodifier::float,1)) as damage
                    FROM montypes
                    LEFT JOIN pokemon.typematchup tm ON montypes.type1id  = tm.defendingtypeid
                    LEFT JOIN pokemon.type attacktype ON tm.attackingtypeid = attacktype.typeid
                    WHERE tm.generationid = """+gen+"""
                    GROUP BY attacktype.typename),\r\n"""
        damage2 = """damage2 as (
                    SELECT DISTINCT attacktype.typename attacker,SUM(coalesce(tm.damagemodifier::float,1)) as damage
                    FROM montypes
                    LEFT JOIN pokemon.typematchup tm ON montypes.type2id  = tm.defendingtypeid
                    LEFT JOIN pokemon.type attacktype ON tm.attackingtypeid = attacktype.typeid
                    WHERE tm.generationid = """+gen+"""
                    GROUP BY attacktype.typename) \r\n"""
        mainSelect = """SELECT damage1.attacker attacktype,SUM(coalesce(damage1.damage,1) * coalesce(damage2.damage,1)) as totaldamage
                    FROM damage1 LEFT JOIN damage2 ON damage1.attacker = damage2.attacker
                    GROUP BY attacktype"""
        matchupInfo = performSQL(monTypes+damage1+damage2+mainSelect)
        printableDict = {4.0:[],2.0:[],1.0:[],.5:[],.25:[],0:[]}
        for type,dmgmodifier in matchupInfo:
            printableDict[dmgmodifier].append(type)
        monTypes = getMonTypes(monID, channel)
        weaknessInfo = monName +" "+ monTypes + ", Gen " +gen+" = \r"
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
    weaknessInfo = weaknessInfo.replace('[','').replace(']','').replace("\'","")
    return weaknessInfo
    

def getAbbrevs():
    abbrevs = performSQL("SELECT DISTINCT gg.gamegroupabbreviation,gg.gamegrouporder FROM pokemon.gamegroup gg INNER JOIN pokemon.game gm ON gg.gamegroupid = gm.gamegroupid ORDER BY gg.gamegrouporder")
    message = "Available games are: "
    for abbrev in abbrevs:
        message += abbrev[0]+", "
    message = message[:len(message)-2]
    return message

def getGames():
    games = performSQL("SELECT gm.gamename,gg.gamegrouporder FROM pokemon.game gm LEFT JOIN pokemon.gamegroup gg ON gm.gamegroupid = gg.gamegroupid ORDER BY gg.gamegrouporder,gm.gamename")
    message = "Available games are: "
    for game in games:
        message += game[0]+", "
    message = message[:len(message)-2]
    return message

def dbConfig(configFile = "chatbot.ini",section="database"):
    config = configparser.ConfigParser()
    config.read(configFile)
    db = {}
    configuration = config.items(section)
    for option in configuration:
        db[option[0]] = option[1]
    return db

def chatMessage(messageString, channel, server):
    server.send(bytes('PRIVMSG #'+ channel + ' :'+messageString+' \r\n', 'utf-8'))

def performSQL(sql):
    dbConn = dbConfig()
    #print("Connecting to database...")
    conn = psycopg2.connect(**dbConn)
    with conn.cursor() as cur:
        conn.set_session(readonly=False, autocommit=True)
        #print("Executing... " +sql)
        cur.execute(sql)
        result = cur.fetchall()
    return result

def setGame(game, channel, server):
    #create an error message if there are no parameters given
    if len(game) < 1:
        message = "Command !pokegame requires a game name or abbreviation as a parameter. Use !gamelist to see a list."
    #if there are parameters, try using it as a game name and fetching an abbreviation
    else:
        #turn the parameters into a gamename string
        gameName = ""
        for word in game:
            gameName += word
            #try using the parameters as an exact match with a game abbreviation
        gameName = gameName.upper()
        selectedGame = performSQL("""SELECT gg.gamegroupname, gg.gamegroupabbreviation,'null',gm.gamename,gm.gameid
                                    FROM pokemon.gamegroup gg
                                    LEFT JOIN pokemon.game gm ON gg.gamegroupid = gm.gamegroupid
                                    WHERE gg.gamegroupabbreviation = '"""+gameName+"' LIMIT 1")
        #if we fail to find a game, try using the parameters as a full game name with levenshtein distance < 5
        if selectedGame == []:
            gameName = gameName.title()
            selectedGame= performSQL("""WITH ldist as (SELECT gg.gamegroupname, gg.gamegroupabbreviation,pokemon.levenshtein(gm.gamename, '"""+gameName+"""')
                                    AS distance,gm.gamename,gm.gameid FROM pokemon.game gm
                                    LEFT JOIN pokemon.gamegroup gg ON gm.gamegroupid = gg.gamegroupid)
                                    SELECT * FROM ldist WHERE distance < 4
                                    ORDER BY distance LIMIT 1""")
        #if we found a game in either query above, find the generation, update the config, and say there was a success!
        if not selectedGame == []:
            groupName,gameAbbrev,throwAwayVariable,gameName,gameid = selectedGame[0]
            updateGame = "UPDATE bot.channel set gameid = "+str(gameid)+" WHERE channelname = '"+channel+"' RETURNING channelid;"
            channelid = performSQL(updateGame)
            message = "Changed the game to "+gameName+"."
        else:
            message = gameName+" is not a valid game. Use !abbrevs for a list of valid abbreviations/games. I wasn't able to change the game to "+gameName+"."
    return message

def getCoverage(coverageTypes,channel):
    gen = getGeneration(channel)
    game = getGame(channel)
    gameID = str(getGameID(channel))
    typeIDs = []
    typeNames = []
    for coverageType in coverageTypes:
        type = performSQL("""WITH ldist AS (SELECT ty.typeid,ty.typename,pokemon.levenshtein(ty.typename,'"""+coverageType+"""')
                            AS distance FROM pokemon.type ty where ty.generationid <="""+gen+""")
                            SELECT * FROM ldist WHERE distance < 3 ORDER BY distance LIMIT 1""")
        if type == []:
            message = coverageType.title()+" is not a valid type in generation "+gen+"."
            return message
        else:
            typeIDs.append(type[0][0])
            typeNames.append(type[0][1])
    monTypes = """WITH montypes as (
                SELECT pokemonid,type1id,type2id
	            FROM pokemon.crosstab('select pt.pokemonid, typeid as type1id, typeid as type2id
                FROM pokemon.pokemontype pt
                LEFT JOIN pokemon.pokemongameavailability pga ON pt.pokemonid = pga.pokemonid
                LEFT JOIN pokemon.game gm ON pga.gameid = gm.gameid
                WHERE pt.generationid ="""+gen+"""
                AND gm.gameid = """+gameID+"""
                AND pga.pokemonavailabilitytypeid != 18
                GROUP BY pt.pokemonid,type1id,type2id ORDER BY pt.pokemonid,type1id,type2id')
		        AS ct( pokemonid int, type1id int, type2id int)),"""
    damage1 = """damage1 AS (\r\n"""
    damage1 += """SELECT montypes.pokemonid,mon.pokemonname,"""
    for typeName in typeNames:
        damage1 += """CASE WHEN (montypes.pokemonid = 343 AND """+typeName+"""1.attackingtypeid NOT IN(2,10,13,14,16)) THEN 0 ELSE """
        damage1 += typeName+"1.damagemodifier::float END as "+typeName+"damage"
        if typeNames.index(typeName) < len(typeNames)-1:
            damage1 += ","
        elif typeNames.index(typeName) == len(typeNames)-1:
            damage1 += "\r\n"
    damage1 += """ FROM montypes\r\n
                        LEFT JOIN pokemon.pokemon mon ON montypes.pokemonid = mon.pokemonid \r\n"""
    for typeName in typeNames:
        damage1 += "LEFT JOIN pokemon.typematchup "+typeName+"1 ON montypes.type1id = "+typeName+"1.defendingtypeid\r\n"
    damage1 += " WHERE "
    for typeName in typeNames:
        damage1 += typeName+"1.attackingtypeid = "+str(typeIDs[typeNames.index(typeName)])+"\r\n AND "
        damage1 += typeName+"1.generationid = "+gen+" "
        if typeNames.index(typeName) < len(typeNames)-1:
            damage1 += "\r\n AND "
    damage1 += "\r\nGROUP BY montypes.pokemonid,mon.pokemonname,"
    for typeName in typeNames:
        damage1 += typeName+"damage"
        if typeNames.index(typeName) < len(typeNames)-1:
            damage1 += ","
        elif typeNames.index(typeName) == len(typeNames)-1:
            damage1 += "),\r\n "
    damage2 = "damage2 as (SELECT montypes.pokemonid,mon.pokemonname,"""
    for typeName in typeNames:
        damage2 += """CASE WHEN (montypes.pokemonid = 343 AND """+typeName+"""2.attackingtypeid NOT IN(2,10,13,14,16)) THEN 0 ELSE """
        damage2 += typeName+"2.damagemodifier::float END as "+typeName+"damage"
        if typeNames.index(typeName) < len(typeNames)-1:
            damage2 += ","
    damage2 += """\r\n FROM montypes\r\n
                        LEFT JOIN pokemon.pokemon mon ON montypes.pokemonid = mon.pokemonid \r\n"""
    for typeName in typeNames:
        damage2 += "LEFT JOIN pokemon.typematchup "+typeName+"2 ON montypes.type2id = "+typeName+"2.defendingtypeid\r\n"
    damage2 += " WHERE "
    for typeName in typeNames:
        damage2 += typeName+"2.attackingtypeid = "+str(typeIDs[typeNames.index(typeName)])+"\r\n AND "
        damage2 += typeName+"2.generationid = "+gen+" "
        if typeNames.index(typeName) < len(typeNames)-1:
            damage2 += "\r\n AND "
    damage2 += "\r\n GROUP BY montypes.pokemonid,mon.pokemonname,"
    for typeName in typeNames:
        damage2 += typeName+"damage"
        if typeNames.index(typeName) < len(typeNames)-1:
            damage2 += ","
        elif typeNames.index(typeName) == len(typeNames)-1:
            damage2 += ") "
    preSelect = "SELECT damage, count(*) FROM (\r\n"
    mainSelect = "SELECT damage1.pokemonid, GREATEST("
    for typeName in typeNames:
        mainSelect += "SUM(coalesce(damage1."+typeName+"damage,1) * coalesce(damage2."+typeName+"damage,1))"
        if typeNames.index(typeName) < len(typeNames)-1:
            mainSelect += ",\r\n "
        elif typeNames.index(typeName) == len(typeNames)-1:
            mainSelect += ") as damage FROM damage1 LEFT JOIN damage2 ON damage1.pokemonid = damage2.pokemonid "
    mainGroup = "GROUP BY damage1.pokemonid "
    postSelect = ") AS mondamage GROUP BY damage ORDER BY damage ASC\r\n"
    selectString = monTypes+damage1+damage2+preSelect+mainSelect+mainGroup+postSelect
    pokemonList = performSQL(selectString)
    coverageString = "Types: "
    for name in typeNames:
        coverageString += name
        if typeNames.index(name) < len(typeNames)-1:
            coverageString += ", "
    coverageString += " - "
    pokemonString = "-- Obstacles: "
    coverageString += " ("+game+"): "
    for array in pokemonList:
        coverageString += str(array[0]).replace(".0",".").replace("0.5",".5").replace("0.","0").replace("1.","1").replace("2.","2").replace("4.","4")+"x: "+str(array[1])
        if pokemonList.index(array) < len(pokemonList)-1:
            coverageString += " // "
    if pokemonList[0][0] < .5 and pokemonList[1][0] < .5:
        pokemonString = " -- Obstacles < 1x"
        limit = pokemonList[0][1]+pokemonList[1][1]
    elif pokemonList[0][0] < 1 and pokemonList[1][0] < 1:
        pokemonString = " -- Obstacles < 1x"
        limit = pokemonList[0][1]+pokemonList[1][1]
    elif pokemonList [0][0] < 1 and pokemonList [1][0] == 1:
        pokemonString = " -- Obstacles"
        limit = pokemonList[0][1]
    elif pokemonList[0][0] == 1:
        pokemonString = " -- Top 5 1x Threats"
        limit = 5
    if int(limit) > 12:
        pokemonString += " (Limit 12): "
        limit = 12
    else:
        pokemonString += ": "
    bstSelect = "SELECT damage1.pokemonid, mon.pokemonname, GREATEST("
    for typeName in typeNames:
        bstSelect += "SUM(coalesce(damage1."+typeName+"damage,1) * coalesce(damage2."+typeName+"damage,1))"
        if typeNames.index(typeName) < len(typeNames)-1:
            bstSelect += ",\r\n "
        elif typeNames.index(typeName) == len(typeNames)-1:
            bstSelect += """) as damage\r\n
                            FROM damage1\r\n
                            LEFT JOIN damage2 ON damage1.pokemonid = damage2.pokemonid\r\n
                            LEFT JOIN pokemon.pokemon mon ON damage1.pokemonid = mon.pokemonid\r\n"""
    monBST = """, monBST as (\r\n
                SELECT mon.pokemonid monid,\r\n
                    mon.pokemonname as monname,\r\n
                    ps.generationid gen,\r\n
                    sum(ps.pokemonstatvalue) as bst\r\n
                FROM pokemon.pokemonstat ps\r\n
                LEFT JOIN pokemon.pokemon mon ON ps.pokemonid = mon.pokemonid\r\n
                WHERE ps.generationid <= """+gen+"""GROUP BY monid,monname,gen ORDER BY gen DESC, monid, monname) \r\n"""
    preWith = "WITH monDamageQuery as (\r\n"
    postWith = ")"
    bstGroup = " GROUP BY damage1.pokemonid,mon.pokemonname \r\n"
    bstOrder = " ORDER BY damage ASC\r\n"""
    realSelect = """SELECT damage, bst, monDamageQuery.pokemonname, monBST.gen FROM monDamageQuery
                    LEFT JOIN monBST ON monDamageQuery.pokemonid = monBST.monid
                    GROUP BY damage, bst, monDamageQuery.pokemonname, monBST.gen
                    ORDER BY damage ASC, bst DESC, monDamageQuery.pokemonname, monBST.gen"""
    coverageQuery = monTypes+damage1+damage2+bstSelect+bstGroup+bstOrder
    sql = preWith+coverageQuery+postWith+monBST+realSelect
    pokemonBSTList = []
    pokemonIDs = performSQL(sql)
    if len(pokemonIDs) == 0:
        pokemonString += "None"
    for obstacle in pokemonIDs:
        if len(pokemonBSTList) < int(limit):
            obstacleName = obstacle[2]
            if not obstacleName in pokemonBSTList:
                pokemonBSTList.append(obstacleName)
                pokemonString += obstacleName+", "
    pokemonString = pokemonString[0:len(pokemonString)-2]
    coverageString += pokemonString
    coverageString = coverageString.replace(" Form)",")")
    return coverageString

def getGameID(channel):
    gameID = performSQL("""SELECT gameid FROM bot.channel WHERE channelname = '"""+channel+"'")[0][0]
    return gameID

def getGame(channel):
    game = performSQL("""SELECT gg.gamegroupabbreviation FROM bot.channel ch
                    LEFT JOIN pokemon.game gm ON ch.gameid = gm.gameid
                    LEFT JOIN pokemon.gamegroup gg ON gm.gamegroupid = gg.gamegroupid
                    WHERE ch.channelname = '"""+channel+"'")[0][0]
    return game

if __name__ == "__main__":
    main()