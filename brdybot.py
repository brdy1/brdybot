#this is for opening the configuration file
import sys
import configparser
from typing import Dict
import requests
import json
import pandas as pd
from app import *
import crosstab.crosstab
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

dbschema='pokemon,bot'
engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5432/postgres',connect_args={'options': '-csearch_path={}'.format(dbschema)})
Base = declarative_base(engine)

Base.metadata.create_all(engine)

def main():
    conn, token, user, readbuffer, server = connectionVariables()
    session = Session(engine)
    deletedchannels = session.query(ChannelDeletion.channelid).all()
    channels = session.query(Channel.channelname).filter(Channel.channelid.notin_(deletedchannels)).all()
    # channels = [('brdy',)]
    session.close()
    commandDict = getCommands()
    for channel in channels:
        channel = channel[0]
        operators = getOperants(channel)
        threading.Thread(target=ircListen, args=(conn, token, user, channel, server, operators, commandDict)).start()
        sleep(2)

def getOperants(channel):
    operators = []
    session = Session(engine)
    operants = session.query(Operant.operantname).select_from(Operant).\
                join(ChannelOperant,Operant.operantid == ChannelOperant.operantid).\
                join(Channel,ChannelOperant.channelid == Channel.channelid).\
                filter(Channel.channelname == channel).all()
    session.close()
    print(operants)
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
            message = None
            response = server.recv(2048).decode('utf-8')
            if len(response) == 0:
                break
            if "PING" in str(response):
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
                if ("!" in command[0:1]) and (command[1:] in list(commandDict.keys())) and permissions:
                    print("\r\n\r\nreceived command:")
                    commandid = commandDict[command[1:]]
                    commandrequestid = logCommand(commandid,channel,username,parameters)
                    message = None
                    print(commandrequestid)
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
    session = Session(engine)
    commands = session.query(Command.commandid,Command.commandname).order_by(Command.commandname).all()
    session.close()
    commandDict = {}
    for command in commands:
        commandDict[command[1]] = command[0]
    return commandDict

def doCommand(commandrequestid):
    conn, token, botName, readbuffer, server = connectionVariables()
    session = Session(engine)
    parameters = []
    select = [  ChannelCommandRequest.channelcommandrequestid,
                Command.commandname,
                Channel.channelname,
                Operant.operantid
                ]
    ccr = session.query(*select).select_from(ChannelCommandRequest).\
                join(Command).\
                join(Channel).\
                join(Operant).\
                filter(ChannelCommandRequest.channelcommandrequestid == commandrequestid).all()
    ccrp = session.query(ChannelCommandRequestParameter.channelcommandrequestparameter).\
                select_from(ChannelCommandRequest).\
                join(ChannelCommandRequestParameter).\
                join(Command).\
                join(Channel).\
                filter(ChannelCommandRequestParameter.channelcommandrequestid == commandrequestid).all()
    session.close()
    id,command,channel,username = ccr[0]
    for parameter in ccrp:
        parameters.append(parameter[0])
    if command == "mon":
        message = getMonInfo(parameters,channel)
    elif command == "move":
        message = getMoveInfo(parameters,channel)
    elif command == "ability":
        message = getAbilityInfo(parameters,channel)
    # elif command == "xp":
    #     message = getXPYield()
    elif command == "bst":
        monName = combineParameters(parameters)
        monID,monName = getMonID(monName,channel)
        if monID == None:
            message = monName
        else:
            game = getGame(channel)
            message = monName + " ("+game+"): " + getMonBST(monID,channel)
    elif command == "learnset":
        monName = combineParameters(parameters)
        monID,monName = getMonID(monName,channel)
        if monID == None:
            message = monName
        else:
            game = getGame(channel)
            message = monName + " ("+game+"): "+getMonMoves(monID,channel)
    elif command == "type":
        monName = combineParameters(parameters)
        monID,monName = getMonID(monName,channel)
        if monID == None:
            message = monName
        else:
            game = getGame(channel)
            message = monName + " ("+game+"): " + getMonTypes(monID,channel).replace("(","").replace(")","")
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
    elif command == "removeops":
        message = removeOperants(parameters,channel)
    elif command == "listops":
        message = listOperants(channel)
    elif command == "join" and channel == "brdybot":
        message = addClient(conn,token,botName,username,server)
    elif command == "brdybotleave" and channel == username:
        message = removeClient(username)
    elif command == "pokecom":
        commandsList = getCommands()
        commandsList = list(commandsList.keys())
        commandsList.remove("join")
        commands = ""
        for com in commandsList:
            commands += "!"+com+", "
        commands = commands[0:len(commands)-2]
        message = "Available commands are " + commands + ". Use !help <command> for command info."
    elif command == "help":
         message = commandHelp(parameters)
    elif command == "botinfo":
        message = "Visit https://www.twitch.tv/brdybot/about"
    return message

def commandHelp(command):
    session = Session(engine)
    if len(command) < 1:
        message = "Command !help requires a command as a parameter. Use !pokecom to see list of commands."
        return message
    elif len(command) > 1:
        message = "Too many parameters in !help command. Use '!help <command>'"
        return message
    else:
        command = command[0]
    commandQuery = session.query(Command.commandname,Command.commanddescription).\
                    select_from(Command).\
                    order_by(func.levenshtein(Command.commandname,command)).\
                    first()
    comName,comDesc = commandQuery
    message = "Command !"+comName+": "+comDesc
    return message

def storeMessage(message,ccrid):
    message = message.replace("'","''")
    session = Session(engine)
    stmt = update(ChannelCommandRequest).\
            where(ChannelCommandRequest.channelcommandrequestid == ccrid).\
            values(channelcommandrequestreturn=message).\
            returning(ChannelCommandRequest.channelcommandrequestid)
    success = session.execute(stmt)
    session.commit()
    session.close()
    return success

def logException(commandrequestid, exception, channel):
    channelid = getChannelID(channel)
    if not commandrequestid:
        commandrequestid = None
    session = Session(engine)
    errortype = session.query(ErrorType.errortypeid).filter(ErrorType.errortypename == exception).first()
    if errortype != []:
        errortype = errortype[0]
    else:
        errortype = session.query(ErrorType.errortypeid).filter(ErrorType.errortypename == "OtherError").first()
    if commandrequestid:
        stmt = insert(ChannelError).\
                    values(channelcommandrequestid=commandrequestid, errortypeid=errortype)
    else:
        stmt = insert(ChannelError).\
                    values(errortypeid=errortype)
    channelerrorid = session.execute(stmt).inserted_primary_key[0]
    session.commit()
    session.close()
    traceback.print_exc()
    print(" with channelerrorid = "+str(channelerrorid))
    commandDict = getCommands()
    conn, token, user, readbuffer, server = connectionVariables()
    operators = getOperants(channel) 
    threading.Thread(target=ircListen, args=(conn, token, "brdybot", channel, server, operators, commandDict)).start()
    sys.exit()

def getChannelID(channel):
    session = Session(engine)
    channelid = session.query(Channel.channelid).\
                filter(Channel.channelname == channel).first()
    session.close()
    return channelid

def logCommand(commandid,channelname,operantname,parameters):
    session = Session(engine)
    commandname = session.query(Command.commandname).filter(Command.commandid == commandid).first()[0]
    if commandid == 9:
        success = addOperants([operantname],channelname)
    channelid = getChannelID(channelname)
    operantid = session.query(Operant.operantid).filter(Operant.operantname == operantname).first()[0]
    print("\r\n________________________________________________________________________________________________________")
    print("Received the "+commandname+" command in channel "+channelname+" from user "+operantname+". Parameters: "+str(parameters)+"\r\n")
    stmt = insert(ChannelCommandRequest).\
                            values(commandid=commandid,channelid=channelid,operantid=operantid)
    result = session.execute(stmt)
    ccrid = result.inserted_primary_key[0]
    session.commit()
    for parameter in parameters:
        parameter = parameter.replace("'","''")
        parameterid = insert(ChannelCommandRequestParameter).\
                    values(channelcommandrequestid=ccrid,channelcommandrequestparameter=parameter).\
                    returning(ChannelCommandRequestParameter.channelcommandrequestparameterid)
        result = session.execute(parameterid)
    session.commit()
    session.close()
    return ccrid

def addOperants(parameters, channel):
    channelid = getChannelID(channel)
    session = Session(engine)
    note = ""
    exists = False
    for parameter in parameters:
        parameter = parameter.lower()
        operantid = session.query(Operant.operantid).filter(Operant.operantname == parameter).first()
        if operantid == None:
            operantid = insert(Operant).values(operantname=parameter)
            operantid = session.execute(operantid).inserted_primary_key[0]
            session.commit()
            session.close()
        else:
            operantid = operantid[0]
        channeloperantid = session.query(ChannelOperant.channeloperantid).select_from(ChannelOperant).\
                        join(Channel,ChannelOperant.channelid == Channel.channelid).\
                        join(Operant,ChannelOperant.operantid == Operant.operantid).\
                        filter(Channel.channelname == channel,ChannelOperant.operantid == operantid).first()
        if channeloperantid == None:
            channeloperantid = insert(ChannelOperant).values(channelid=channelid,operantid=operantid,operanttypeid=2)
            channeloperantid = session.execute(channeloperantid).inserted_primary_key[0]
            session.commit()
            session.close()
        else:
            note = " Some listed users were already bot users in channel "+channel+"."
    message = "Successfully added bot users to configuration."+note
    session.commit()
    session.close()
    return message

def removeOperants(parameters, channel):
    message = "User(s) "
    session = Session(engine)
    for parameter in parameters:
        parameter = parameter.lower()
        if parameter != channel:
            channelid = getChannelID(channel)
            operantid = session.query(Operant.operantid).\
                        filter(Operant.operantname == parameter).\
                            first()
            session.query(ChannelOperant).\
                    filter(ChannelOperant.channelid==channelid,ChannelOperant.operantid==operantid).\
                        delete()
            session.commit()    
            session.close()
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
    session = Session(engine)
    channelid = getChannelID(username)
    operantid = session.query(Operant.operantid).filter(Operant.operantname == username).first()
    if channelid == []:
        channelid = insert(Channel).values(channelname=username,gameid=10).returning(Channel.channelid)
        channelid = session.execute(channelid).inserted_primary_key[0]
        session.commit()
        session.close()
    if operantid == []:
        operantid = insert(Operant).values(operantname=username).returning(Operant.operantid)
        operantid = session.execute(operantid).inserted_primary_key[0]
        session.commit()
        session.close()
    operanttypeid = session.query(ChannelOperant.operanttypeid).\
                        filter(ChannelOperant.channelid == channelid, ChannelOperant.operantid == operantid).first()
    if operanttypeid == []:
        channeloperantid = insert(ChannelOperant).values(channelid=channelid,operantid=operantid,operanttypeid=1).returning(ChannelOperant.channeloperantid)
        channeloperantid = session.execute(channeloperantid)
        session.commit()
        session.close()
        message = username+""" - You have been successfully added to the channel list.
                                Game has been set to FireRed. Use !pokegame in your channel to change the game.
                                Note that I do store usernames and command usage records in the database for use in feature improvement.
                                Your username will NEVER be shared with anyone for any reason.
                                Use !brdybotleave in your channel to remove yourself from my channel list."""
        operants = getOperants(username)
        commandDict = getCommands()
        threading.Thread(target=ircListen, args=(conn, token, botName, username, server, operants,commandDict)).start()
    elif operanttypeid[0][0] == 1:
        message = username+" - I should be operating in your channel. If I'm not, message brdy on Discord to correct the error."
    session.close()
    return message

def removeClient(channel):
    session = Session(engine)
    channelid = getChannelID(channel)
    channelid = insert(ChannelDeletion).values(channelid=channelid).returning(channelid)
    session.commit()
    session.close()
    message = channel+" - Successfully removed you from the channel list."
    return message

def getMoveID(moveName):
    session = Session(engine)
    moveShtein = func.least(func.levenshtein(Move.movename,moveName),func.levenshtein(MoveNickname.movenickname,moveName)).label("moveShtein")
    moveID = session.query(Move.moveid).join(MoveNickname,Move.moveid == MoveNickname.moveid).order_by(moveShtein).filter(moveShtein < 5).limit(1).first()
    session.close()
    moveID = str(moveID[0])
    return moveID

def combineParameters(parameters):
    name = ""
    for parameter in parameters:
        name += parameter + " "
    name = name[:len(name)-1].title()
    return name

def getMonID(monName,channel):
    monName = monName.replace("'","''")
    print("GetMonID MonName: "+monName)
    session = Session(engine)
    gameid = getGameID(channel)
    gameName = getGame(channel)
    monShtein = (func.least(func.pokemon.levenshtein(Pokemon.pokemonname,monName),func.pokemon.levenshtein(PokemonNickname.pokemonnickname,monName))).label("monShtein")
    monID,monAvailability = session.query(Pokemon.pokemonid,PokemonGameAvailability.pokemonavailabilitytypeid).\
                select_from(Pokemon).\
                join(PokemonNickname,Pokemon.pokemonid == PokemonNickname.pokemonid, isouter = True).\
                join(PokemonGameAvailability,Pokemon.pokemonid == PokemonGameAvailability.pokemonid).\
                filter(monShtein < 5,PokemonGameAvailability.gameid == gameid).\
                order_by(monShtein).\
                first()
    if monID == []:
        errorString = "Could not find Pokemon "+monName+"."
        return None,errorString
    elif monAvailability == (18):
        errorString = monName + " is not available in "+gameName+"."
        return None,errorString
    monID = str(monID)
    print("GetMonID MonID: "+str(monID))
    monName = session.query(Pokemon.pokemonname).filter(Pokemon.pokemonid == monID).first()
    monName = str(monName[0])
    session.close()
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
    session = Session(engine)
    availability = session.query(PokemonGameAvailability.pokemonavailabilitytypeid).\
                        join(Game,PokemonGameAvailability.gameid == Game.gameid).\
                        join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                        filter(PokemonGameAvailability.pokemonid == monID,GameGroup.gamegroupabbreviation == game).\
                        distinct().all()
    if availability[0][0] == 18:
        gameID = getGameID(channel)
        gameName = session.query(Game.gamename).filter(Game.gameid == gameID).first()[0]
        message = monName + " is not available in " + gameName + "."
        return message
    #this section gets all the info to be compiled in a string at the end of this function
    monsel = [  Pokemon.pokemonname,
                Pokemon.pokemonpokedexnumber,
                LevelingRate.levelingratename,
                Pokemon.pokemoncapturerate
                ]
    monName,monDex,monGrowth,monCaptureRate = session.query(*monsel).\
                                                select_from(Pokemon).\
                                                join(LevelingRate,Pokemon.levelingrateid == LevelingRate.levelingrateid).\
                                                filter(Pokemon.pokemonid == monID).first()
    session.close()
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
    session = Session(engine)
    rate = session.query(LevelingRate.levelingratename).join(Pokemon,Pokemon.levelingrateid == LevelingRate.levelingrateid).filter(Pokemon.pokemonid == monID).first()
    rate = str(rate[0])
    session.close()
    return rate

def getGeneration(channel):
    session = Session(engine)
    generation = session.query(Generation.generationid).select_from(Channel).\
                            join(Game,Channel.gameid == Game.gameid).\
                            join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                            join(Generation,GameGroup.generationid == Generation.generationid).\
                            filter(Channel.channelname == channel).first()
    generation = str(generation[0])
    session.close()
    return generation

def getMonDex(monID, channel):
    session = Session(engine)
    dex = session.query(Pokemon.pokemonpokedexnumber).filter(Pokemon.pokemonid == monID).first()
    monDex = str(dex[0])
    return monDex

def getMonTypes(monID, channel):
    gen = getGeneration(channel)
    typeList = []
    url = "http://127.0.0.1:5000/api/v1.0/pokemon"
    data = requests.get(url+"?id="+monID+"&gen="+gen)
    data = data.json()
    typeList = list(data[monID]['types'].keys())
    for mType in typeList:
        if data[monID]['types'][mType] == 'false':
            typeList.remove(mType)
    #if there are two types, store as (Type1/Type2)
    types = "("+str(typeList[0])
    if len(typeList) > 1:
        types += "/"+str(typeList[1])+")"
    #otherwise, store as (Type)
    else:
        types += ")"
    return types

def getMonBST(monID, channel):
    gen = getGeneration(channel)
    session = Session(engine)
    bstAl = session.query(func.sum(PokemonStat.pokemonstatvalue)).\
                filter(PokemonStat.pokemonid == monID,PokemonStat.generationid <= gen).\
                group_by(PokemonStat.generationid).\
                order_by(PokemonStat.generationid).\
                    first()
    monBST = str(bstAl[0])
    return monBST

def getCaptureRate(captureRate,channel):
    #this formula approximates the catch rate to within about .1% and will work for future catch rates not currently being used
    captureRate = 0.0000000000566758779982193 * math.pow(captureRate,5) - 0.0000000427601042779669*math.pow(captureRate,4) + 0.0000125235963016363*math.pow(captureRate,3) - 0.00191121035271638*math.pow(captureRate,2) + 0.311407303213974*captureRate + 0.846589688792571
    captureRate = round(captureRate, 1)
    captureRate = str(captureRate)
    return captureRate

def getXPYield(monID, channel,enemylevel,monlevel):
    gen = getGeneration(channel)
    gen = int(gen)
    session = Session(engine)
    try:
        xpyieldAl = session.query(PokemonExperienceYield.experienceyieldvalue,PokemonExperienceYield.generationid).\
                    filter(PokemonExperienceYield.pokemonid == int(monID), PokemonExperienceYield.generationid <= gen).\
                    order_by(PokemonExperienceYield.generationid.desc()).\
                        first()
        print(xpyieldAl)
        monyield = xpyieldAl[0]
        xp = monyield*enemylevel/7
        xp=str(int(round(xp,0)))
    except:
        traceback.print_exc()
        xp='unknown'
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
        url = "http://127.0.0.1:5000/api/v1.0/move?name="
        moveInfo = requests.get(url+moveName)
        moveInfo = moveInfo.json()
        mvName = str(list(moveInfo.keys())[0])
        moveType = moveInfo[mvName][gen]['type']
        if moveInfo[mvName][gen]['contact'] == 'true':
            moveContact = 'C'
        else:
            moveContact = 'NC'
        accuracy = str(moveInfo[mvName][gen]['accuracy'])
        description = str(moveInfo[mvName][gen]['description'])
        power = str(moveInfo[mvName][gen]['power'])
        pp = str(moveInfo[mvName][gen]['pp'])
        priority = str(moveInfo[mvName][gen]['priority'])
        category = str(moveInfo[mvName][gen]['category'])
        info = mvName+" - Gen " +gen+ ": ("+moveType+", "+category+", "+moveContact+") | PP: "+pp+" | Power: "+power+" | Acc.: "+accuracy+" | Priority: "+priority+" | Summary: "+description
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
        return weaknessInfo
    monName = combineParameters(parameters)
    monID,monName = getMonID(monName,channel)
    if monID == None:
        weaknessInfo = "I was not able to find weakness info for that Pokemon."
        return weaknessInfo
    gen = getGeneration(channel)
    print(gen)
    url = "http://127.0.0.1:5000/api/v1.0/weakness"
    data = requests.get(url+"?id="+monID+"&gen="+gen+"&channel="+channel)
    monTypes = getMonTypes(monID,channel)
    weaknessDict = data.json()
    info = ""
    for bracket in weaknessDict.keys():
        if len(weaknessDict[bracket]) > 0:
            info += bracket+"x: "
            for moveType in weaknessDict[bracket]:
                info += moveType
                if weaknessDict[bracket].index(moveType) < len(weaknessDict[bracket])-1:
                    info += ", "
                elif weaknessDict[bracket].index(moveType) == len(weaknessDict[bracket])-1:
                    info += " // "
    weaknessInfo = monName +" "+ monTypes + ", Gen " +gen+" = \r"+info
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
            gameName += word+" "
            #try using the parameters as an exact match with a game abbreviation
        gameAbbr = gameName.upper().replace("'","''").replace(" ","")
        selectedGame = performSQL("""SELECT gg.gamegroupname, gg.gamegroupabbreviation,'null',gm.gamename,gm.gameid
                                    FROM pokemon.gamegroup gg
                                    LEFT JOIN pokemon.game gm ON gg.gamegroupid = gm.gamegroupid
                                    WHERE gg.gamegroupabbreviation = '"""+gameAbbr+"' LIMIT 1")
        #if we fail to find a game, try using the parameters as a full game name with levenshtein distance < 5
        if selectedGame == []:
            fullGame = gameName.title().replace("'","''")
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
            message = game+" is not a valid game. Use !abbrevs for a list of valid abbreviations/games. I wasn't able to change the game to "+game+"."
    return message

def getCoverage(coverageTypes,channel):
    typeIDs = []
    gen = getGeneration(channel)
    for coverageType in coverageTypes:
        type = performSQL("""WITH ldist AS (SELECT ty.typeid,ty.typename,pokemon.levenshtein(ty.typename,'"""+coverageType+"""')
                            AS distance FROM pokemon.type ty where ty.generationid <="""+gen+""")
                            SELECT * FROM ldist WHERE distance < 3 ORDER BY distance LIMIT 1""")
        if type == []:
            message = coverageType.title()+" is not a valid type in generation "+gen+"."
            return message
        else:
            typeIDs.append(str(type[0][0])+";")
    typesList = ""
    for typeid in typeIDs:
        typesList += str(typeid)
    typesList = typesList[0:len(typesList)-1]
    url = "http://127.0.0.1:5000/api/v1.0/coverage/"
    info = requests.get(url+typesList+"?channel="+channel)
    
    return info.text

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