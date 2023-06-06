import math
from random import Random
from flask import Flask
from flask import session as sesh
from flask_restful import Api, request
from sqlalchemy.orm import Session,aliased
from sqlalchemy import create_engine, func, update, delete, and_, or_, null, case, literal_column
from sqlalchemy.dialects.postgresql import aggregate_order_by, insert
from werkzeug.routing import BaseConverter
from schema import *
import configparser
import pandas as pd
import requests
import traceback
from itertools import combinations


#################################################
# Flask Setup
#################################################
app = Flask(__name__)

api = Api(app)

#################################################
# App Routes ####################################
#################################################

@app.route("/api/v2.0/")
def welcome():
    session = Session(engine)
    """List available API routes."""
    commands = session.query(Command.commandname,CommandType.commandtypename).\
        join(CommandType, CommandType.commandtypeid == Command.commandtypeid).\
        order_by(Command.commandname).\
        all()
    commandlist = "Available Routes:<br/>"
    session.close()
    for command in commands:
        commandlist =+ "/api/v2.0/"+command+"<br/>"
    return commandlist

################
## Bot Routes ##
################
@app.route("/api/v2.0/abbrevs/")
def getAbbrevs():
    session = Session(engine)
    message = "Available game abbreviations: "
    try:
        abbreviations = session.query(GameGroup.gamegroupabbreviation).join(Game).order_by(GameGroup.gamegrouporder).distinct().all()
    except:
        traceback.print_exc()
    finally:
        session.close()
    for abbrev in abbreviations:
        message+= abbrev[0]+", "
    message = message[0:len(message)-2]
    # print(message)
    return {'message':message,'returnid':None}

@app.route("/api/v2.0/ability/<abilityname>")
def getAbility(abilityname):
    twitchuserid = int(request.args.get("twitchuserid"))
    try:
        session = Session(engine)
        gen = session.query(GameGroup.generationid).join(Game).join(Channel).filter(Channel.twitchuserid==twitchuserid).first()[0]
        abilityShtein = func.levenshtein(Ability.abilityname,abilityname).label("abilityShtein")
        abilityname,abilitydescription,generation,abilityid = session.query(Ability.abilityname,GenerationAbility.abilitydescription,GenerationAbility.generationid,GenerationAbility.abilityid).\
                                            select_from(GenerationAbility).\
                                            join(Ability,GenerationAbility.abilityid == Ability.abilityid).\
                                            filter(GenerationAbility.generationid <= gen).\
                                            order_by(abilityShtein,GenerationAbility.generationid.desc()).first()
    except:
        traceback.print_exc()
    finally:
        session.close()
    message = str(abilityname)+" (Gen "+str(gen)+"): "+str(abilitydescription)
    # print(message)
    return {'message':message,'returnid':abilityid}
    
@app.route("/api/v2.0/botinfo/")
def getBotInfo():
    message = "To add me to your own channel, go to https://www.twitch.tv/popout/brdybot/chat and type !join. Discord: https:discord.gg/8vXVTth6FN . You can see my open source Python code here: https://github.com/brdy1/brdybot"
    return {'message':message,'returnid':None}

@app.route("/api/v2.0/bst/<monname>")
def getBST(monname):
    try:
        session = Session(engine)
        twitchuserid = int(request.args.get("twitchuserid"))
        monShtein = func.least(func.levenshtein(Pokemon.pokemonname,monname.title()),func.levenshtein(PokemonNickname.pokemonnickname,monname.title())).label("monShtein")
        monid,monName,gamegroupname,gen = session.query(Pokemon.pokemonid,Pokemon.pokemonname,GameGroup.gamegroupabbreviation,GameGroup.generationid).\
                        select_from(PokemonGameAvailability).\
                        join(Channel,PokemonGameAvailability.gameid == Channel.gameid).\
                        join(Game,Channel.gameid == Game.gameid).\
                        join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                        join(Pokemon,PokemonGameAvailability.pokemonid == Pokemon.pokemonid).\
                        join(PokemonNickname,Pokemon.pokemonid == PokemonNickname.pokemonid,isouter=True).\
                        filter(PokemonGameAvailability.pokemonavailabilitytypeid != 18,Channel.twitchuserid == twitchuserid).\
                        order_by(monShtein).first()
        generationnotused, bstAl = session.query(PokemonStat.generationid,func.sum(PokemonStat.pokemonstatvalue)).\
                    filter(PokemonStat.pokemonid == monid,PokemonStat.generationid <= gen).\
                    group_by(PokemonStat.generationid).\
                    order_by(PokemonStat.generationid.desc()).\
                        first()
        message = monName+" (Gen "+str(gen)+") BST: "+str(bstAl)
    finally:
        session.close()
    # print(message)
    return {'message':message,'returnid':monid}

@app.route("/api/v2.0/fecoverage/<typelist>")
def getEvolvedCoverage(typelist,twitchuserid=None):
    if not twitchuserid:
        twitchuserid = int(request.args.get("twitchuserid"))
    getCoverage(typelist,twitchuserid=twitchuserid,all=False)

@app.route("/api/v2.0/coverage/<typelist>")
def getCoverage(typelist,twitchuserid=None,all=True):
    session = Session(engine)
    if not twitchuserid:
        twitchuserid = int(request.args.get("twitchuserid"))
    typelist = typelist.replace(",","").split(" ")
    try:
        gameid,generation,ggabbr = session.query(Game.gameid,GameGroup.generationid,GameGroup.gamegroupabbreviation).\
            select_from(Channel).\
            join(Game).\
            join(GameGroup).\
            filter(Channel.twitchuserid == twitchuserid).\
            first()
        typeids = []
        for typename in typelist:
            typeindex = typelist.index(typename)
            typeShtein = func.levenshtein(Type.typename,typename)
            typeid,typename = session.query(Type.typeid,Type.typename).filter(Type.generationid <= generation).order_by(typeShtein).first()
            ### Pull all types and typeids, sort by edit distance, then pull top hit for each edit distance
            typeids.append(typeid)
            typelist[typeindex] = typename
        validSel = [
            PokemonStat.pokemonid
            ,func.max(PokemonStat.generationid).label('gen')
        ]
        validated = session.query(Pokemon.pokemonid).\
            join(PokemonGameAvailability,Pokemon.pokemonid == PokemonGameAvailability.pokemonid).\
            filter(PokemonGameAvailability.gameid == gameid,PokemonGameAvailability.pokemonavailabilitytypeid != 18)
        # print(validated)
        if all: ## If all is true, fetch all pokemon for that generation
            validmons = session.query(*validSel).\
                filter(PokemonStat.pokemonid.in_(validated),PokemonStat.generationid <= generation).\
                    group_by(PokemonStat.pokemonid).subquery()
        else: ## If all is false, fetch only pokemon that don't appear as base pokemon in the evolution info table in any games of the current gen or lower
            validmons = session.query(*validSel).\
                filter(
                    PokemonStat.pokemonid.in_(validated),
                    PokemonStat.generationid <= generation,
                    PokemonStat.pokemonid.notin_(
                        session.query(PokemonEvolutionInfo.basepokemonid).\
                            join(GameGroup,PokemonEvolutionInfo.gamegroupid == GameGroup.gamegroupid).\
                            filter(GameGroup.generationid <= generation)
                        )
                    ).\
                    group_by(PokemonStat.pokemonid).subquery()
        type1 = session.query(PokemonType.generationid,PokemonType.pokemonid,PokemonType.typeid).\
            filter(PokemonType.pokemontypeorder == 1).subquery()
        type2 = session.query(PokemonType.generationid,PokemonType.pokemonid,PokemonType.typeid).\
            filter(PokemonType.pokemontypeorder == 2).subquery()
        montypes = session.query(Pokemon.pokemonid,type1.c.generationid,type1.c.typeid.label('type1id'),type2.c.typeid.label('type2id')).\
            select_from(Pokemon).join(validmons,Pokemon.pokemonid == validmons.c.pokemonid).\
                join(type1,Pokemon.pokemonid == type1.c.pokemonid).\
                join(type2,(Pokemon.pokemonid == type2.c.pokemonid) & (type1.c.generationid == type2.c.generationid),isouter=True).subquery()
        monbsts = session.query(PokemonStat.pokemonid,func.sum(PokemonStat.pokemonstatvalue).label('bst')).join(validmons,(PokemonStat.pokemonid == validmons.c.pokemonid) & (PokemonStat.generationid == validmons.c.gen)).\
            group_by(PokemonStat.pokemonid).subquery()
        tm1 = aliased(TypeMatchup)            
        tm2 = aliased(TypeMatchup)
        # shedinjaOverride = case(
        #                        (
        #                             ((montypes.c.pokemonid == 343) & (tm1.damagemodifier*func.coalesce(tm2.damagemodifier,1) < 2)),
        #                             func.max(literal_column("0.00"))
        #                        ),
        #                        else_=func.max(tm1.damagemodifier*func.coalesce(tm2.damagemodifier,1))
        # )
        attackingdmg = session.query(montypes.c.pokemonid,montypes.c.type1id,montypes.c.type2id,func.max(tm1.damagemodifier*func.coalesce(tm2.damagemodifier,1)).label('dmgmod')).\
            select_from(montypes).\
            join(validmons,(montypes.c.pokemonid == validmons.c.pokemonid) & (montypes.c.generationid == validmons.c.gen)).\
            join(tm1,(montypes.c.type1id == tm1.defendingtypeid) & (tm1.generationid == montypes.c.generationid)).\
            join(tm2,(montypes.c.type2id == tm2.defendingtypeid) & (tm2.generationid == montypes.c.generationid) & (tm1.attackingtypeid == tm2.attackingtypeid),isouter=True).\
            filter(tm1.attackingtypeid.in_(typeids)).\
            group_by(montypes.c.pokemonid,montypes.c.type1id,montypes.c.type2id).subquery()
        coveragecounts = session.query(attackingdmg.c.dmgmod,func.count(attackingdmg.c.pokemonid)).\
            group_by(attackingdmg.c.dmgmod).order_by(attackingdmg.c.dmgmod).all()
        topbsts = session.query(attackingdmg.c.dmgmod,monbsts.c.bst,Pokemon.pokemonname).select_from(attackingdmg).\
            join(monbsts,attackingdmg.c.pokemonid == monbsts.c.pokemonid).\
            join(Pokemon,attackingdmg.c.pokemonid == Pokemon.pokemonid).\
            order_by(attackingdmg.c.dmgmod.asc(),monbsts.c.bst.desc()).all()
    except:
        session.rollback()
        traceback.print_exc()
    finally:
        session.close()
    message = "Types: "
    for typename in typelist: 
        message+=typename+", "
    message=message[0:len(message)-2]+"  ("+ggabbr+") - "
    for dmgbracket,count in coveragecounts:
        message+="["+str(float(dmgbracket)).replace("0.25","¼").replace("0.5","½").replace("0.50","½").replace("0.0","0").replace(".0","")+"x: "+str(count)+"] - "
    message=message[0:len(message)-2]
    mindmg,count = coveragecounts[0]
    if mindmg < .5 and coveragecounts[1][0] < 1:
        count += coveragecounts[1][1]
    if float(mindmg) < 1:
        message+= " -- Obstacles"
        if count > 12:
            message+= " (Limit 12)"
        message+=": "
        topbsts = topbsts[0:count if count < 12 else 12]
    else:
        message+= " -- Top 5 Threats: "
        topbsts = topbsts[0:5]
    for maxdmg,bst,monname in topbsts:
        message+= monname+"("+str(bst)+"), "
    message=message[0:len(message)-2]
    # print(message)
    return {'message':message,'returnid':None}

@app.route("/api/v2.0/ccomb/<parameters>")
@app.route("/api/v2.0/coveragecomb/<parameters>")
def coverageCombinations(parameters):
    twitchuserid = int(request.args.get("twitchuserid"))
    parameters = parameters.split(" ")
    movenumber = int(parameters[0])
    types = parameters[1:]
    if len(types) <= movenumber:
        message = "To work effectively, the !coveragecomb command requires a number of types at least 1 greater than the given number of types to include in the combinations. Add some types or lower the number and try again."
        return {'message':message,'returnid':None}
    typelists = list(combinations(types,movenumber))
    message = ""
    for typelist in typelists:
        coverage = getCoverage(' '.join(typelist),twitchuserid)['message']
        message += coverage+' // '
    return {'message':message,'returnid':None}

@app.route("/api/v2.0/evos/<monname>")
def getEvos(monname,one=False):
    session = Session(engine)
    twitchuserid = int(request.args.get("twitchuserid"))
    try:
        monShtein = func.least(func.levenshtein(Pokemon.pokemonname,monname.title()),func.levenshtein(PokemonNickname.pokemonnickname,monname.title())).label("monShtein")
        monid,monName,gamegroupname,generation = session.query(Pokemon.pokemonid,Pokemon.pokemonname,GameGroup.gamegroupabbreviation,GameGroup.generationid).\
                            select_from(PokemonGameAvailability).\
                            join(Channel,PokemonGameAvailability.gameid == Channel.gameid).\
                            join(Game,Channel.gameid == Game.gameid).\
                            join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                            join(Pokemon,PokemonGameAvailability.pokemonid == Pokemon.pokemonid).\
                            join(PokemonNickname,Pokemon.pokemonid == PokemonNickname.pokemonid,isouter=True).\
                            filter(PokemonGameAvailability.pokemonavailabilitytypeid != 18,Channel.twitchuserid == twitchuserid).\
                            order_by(monShtein).first()
        # print(str(monid)+" "+str(monName)+" "+str(gamegroupname)+" "+str(generation))
        evosel = [Pokemon.pokemonname
                    ,GameGroup.gamegroupname
                    ,PokemonEvolutionInfo.evolutiontypeid
                    ,Item.itemname
                    ,PokemonEvolutionInfo.pokemonevolutionlevel
                    ,Location.locationname
                    ,Move.movename
                    ,PokemonEvolutionInfo.pokemonevolutionstring
                    ]
        preevo = session.query(*evosel).select_from(PokemonEvolutionInfo).\
                                join(Pokemon,PokemonEvolutionInfo.targetpokemonid == Pokemon.pokemonid).\
                                join(GameGroup,PokemonEvolutionInfo.gamegroupid == GameGroup.gamegroupid).\
                                join(PokemonEvolutionItem,PokemonEvolutionInfo.pokemonevolutionid == PokemonEvolutionItem.pokemonevolutionid,isouter=True).\
                                join(Item,PokemonEvolutionInfo.itemid == Item.itemid,isouter=True).\
                                join(Location,PokemonEvolutionInfo.locationid == Location.locationid,isouter=True).\
                                join(Move,PokemonEvolutionInfo.moveid == Move.moveid,isouter=True).\
                                filter(PokemonEvolutionInfo.basepokemonid == monid,GameGroup.generationid <= generation).order_by(GameGroup.gamegrouporder,PokemonEvolutionInfo.evolutiontypeid)
    finally:
        session.close()
    if one:
        pokemonEvolutions = [preevo.first()]
    else:
        pokemonEvolutions = preevo.all()
    evoList = monName
    if not pokemonEvolutions or pokemonEvolutions == [None]:
        evoList += " ("+gamegroupname+"): Does not evolve"
        message = evoList
    else:
        evoList+=" evolutions ("+gamegroupname+"): "
        for evoArray in pokemonEvolutions:
            evoMon = str(evoArray[0])
            evoLevel = str(evoArray[4])
            evoItem = str(evoArray[3])
            evoLocation = str(evoArray[5])
            evoType = evoArray[2]
            evoUnique = str(evoArray[7])
            evoMove = str(evoArray[6])
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
                if evoType == 10 or evoType == 11 or evoType == 17:
                    evoInfo += " while holding " + evoItem
                else:
                    evoInfo += " after being exposed to " + evoItem
            if not evoLocation == 'None':
                evoInfo += " at " + evoLocation
            if not evoMove == 'None':
                evoInfo += " while knowing " + evoMove
            if not evoUnique == 'None':
                evoInfo += " " + evoUnique
            evoList += evoInfo.strip()+" | "
        message = evoList[0:len(evoList)-3]
    # print(message)
    return {'message':message,'returnid':monid}

@app.route("/api/v2.0/gamelist/")
def getGameList():
    session = Session(engine)
    gamelist = session.query(Game.gamename).join(GameGroup).order_by(GameGroup.gamegrouporder).all()
    session.close()
    message = "Available games: "
    for game in gamelist:
        message+= game[0]+", "
    message = message[0:len(message)-2]+". Use !pokegame <gamename> to change the game."
    # print(message)
    return {'message':message,'returnid':None}
    
@app.route("/api/v2.0/help/<commandname>")
def describeCommand(commandname):
    session = Session(engine)
    commandShtein = func.least(func.levenshtein(Command.commandname,commandname),func.levenshtein(Command.commandname,commandname)).label("commandShtein")
    commandsel = [  Command.commandname
                    ,Command.commanddescription
                    ,Command.commandminimumparameters
                    ,Command.commandmaximumparameters
                    ,CommandType.commandtypename
                    ,Command.commandid
                    ]
    try:
        commandname,commanddescription,minparams,maxparams,commandtype,commandid = session.query(*commandsel).\
            join(CommandType,Command.commandtypeid == CommandType.commandtypeid,isouter=True).\
            filter(Command.commandname == commandname,commandname != 'join').\
            order_by(commandShtein).\
            first()
    except:
        session.rollback()
        traceback.print_exc()
    finally:
        session.close()
    message = "Command !"+commandname+": "+commanddescription
    if commandtype is not None:
        message += " Return type: "+commandtype+"."
    if minparams is not None or maxparams is not None:
        message += " Parameters:"
    if minparams is not None:
        message+=" min "+str(minparams).lower()
    if maxparams is not None:
        message+=" max "+str(maxparams).lower()
    return {'message':message,'returnid':commandid}
    
@app.route("/api/v2.0/learnset/<monname>")
def getLearnset(monname,namesFlag=True,twitchuserid=None):
    session = Session(engine)
    if not twitchuserid:
        twitchuserid = int(request.args.get("twitchuserid"))
    try:
        monShtein = func.least(func.levenshtein(Pokemon.pokemonname,monname.title()),func.levenshtein(PokemonNickname.pokemonnickname,monname.title())).label("monShtein")
        monid,monName,gamegroup,generation = session.query(Pokemon.pokemonid,Pokemon.pokemonname,GameGroup.gamegroupid,GameGroup.generationid).\
                            select_from(PokemonGameAvailability).\
                            join(Channel,PokemonGameAvailability.gameid == Channel.gameid).\
                            join(Game,Channel.gameid == Game.gameid).\
                            join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                            join(Pokemon,PokemonGameAvailability.pokemonid == Pokemon.pokemonid).\
                            join(PokemonNickname,Pokemon.pokemonid == PokemonNickname.pokemonid,isouter=True).\
                            filter(PokemonGameAvailability.pokemonavailabilitytypeid != 18,Channel.twitchuserid == twitchuserid).\
                            order_by(monShtein).first()
        pokemonMoves = session.query(Pokemon.pokemonname,GameGroup.gamegroupabbreviation,Move.movename,PokemonMove.pokemonmovelevel).\
                                            select_from(PokemonMove).\
                                            join(Pokemon).\
                                            join(Move).\
                                            join(GameGroup).\
                                            filter(Pokemon.pokemonid == monid,PokemonMove.pokemonmovelevel > 1,PokemonMove.gamegroupid == gamegroup).\
                                            order_by(PokemonMove.pokemonmovelevel).distinct().all()
        # print(str(monid)+" "+str(monName)+" "+str(gamegroup)+" "+str(generation))
        # print(pokemonMoves)
    finally:
        session.close()
    message = monName
    if len(pokemonMoves) > 0:
        if namesFlag:
            message += " learnset ("+pokemonMoves[0][1]+"): "    
        else:
            message += ": Learns moves at "
        for pokemonMove in pokemonMoves:
            pokemonname,gamegroupname,movename,movelevel = pokemonMove
            if namesFlag == True:
                message += movename+" ("+str(movelevel)+"), "
            elif namesFlag == False:
                message += str(movelevel)+", "
        message = message[0:len(message)-2]
    else:
        message+= ": Does not learn moves."
    # print(message)
    return {'message':message,'returnid':monid}

@app.route("/api/v2.0/lss/<monname>")
@app.route("/api/v2.0/learnsetshort/<monname>")
def getLearnsetShort(monname):
    twitchuserid = int(request.args.get("twitchuserid"))
    message = getLearnset(monname,namesFlag=False,twitchuserid=twitchuserid)
    # print(message)
    return message
    
@app.route("/api/v2.0/level/<parameters>")
def getLevelRequirements(parameters):
    session = Session(engine)
    growth,startlvl,endlvl = parameters.lower().replace('-',' ').replace('m s','m-s').replace('m f','m-f').replace('o f','o-f').split(" ")
    startlvl = int(startlvl)
    endlvl = int(endlvl)
    # print(growth)
    # print(startlvl)
    # print(endlvl)
    try:
        growthShtein = func.levenshtein(LevelingRate.levelingratename,growth).label("growthShtein")
        rateid,rate = session.query(LevelingRate.levelingrateid,LevelingRate.levelingratename).order_by(growthShtein).first()
        lvlSel = [LevelingRateLevelThreshold.levelingratelevelthresholdlevel
                    ,LevelingRateLevelThreshold.levelingratelevelthresholdexperience
                    ]
        startlvl,startxp = session.query(*lvlSel).\
            filter(LevelingRateLevelThreshold.levelingratelevelthresholdlevel == startlvl,LevelingRateLevelThreshold.levelingrateid == rateid).first()
        endlvl,endxp = session.query(*lvlSel).\
            filter(LevelingRateLevelThreshold.levelingratelevelthresholdlevel == endlvl,LevelingRateLevelThreshold.levelingrateid == rateid).first()
    finally:
        session.close()
    message = rate+": Level "+str(startlvl)+"-"+str(endlvl)+" = "+str(int(float(endxp)-float(startxp)))+" xp."
    return {'message':message,'returnid':rateid}

@app.route("/api/v2.0/listops/")
def listOps():
    session = Session(engine)
    twitchuserid = int(request.args.get("twitchuserid"))
    try:
        operants = session.query(TwitchUser.twitchusername).\
                select_from(ChannelOperant).\
                join(TwitchUser,ChannelOperant.operanttwitchuserid == TwitchUser.twitchuserid).\
                filter(ChannelOperant.channeltwitchuserid == twitchuserid).all()
    finally:
        session.close()
    message = "Users with permissions: "
    for user in operants:
        message+= user[0]+", "
    message = message[0:len(message)-2]
    # print(message)
    return {'message':message,'returnid':None}

@app.route("/api/v2.0/mon/<monname>")
def getMon(monname):
    #print(monname)
    session = Session(engine)
    twitchuserid = int(request.args.get("twitchuserid"))
    try:
        monShtein = func.least(func.levenshtein(Pokemon.pokemonname,monname.title()),func.levenshtein(PokemonNickname.pokemonnickname,monname.title())).label("monShtein")
        monid,monName,gamegroup,gamegroupname,generation = session.query(Pokemon.pokemonid,Pokemon.pokemonname,GameGroup.gamegroupid,GameGroup.gamegroupname,GameGroup.generationid).\
                            select_from(PokemonGameAvailability).\
                            join(Channel,PokemonGameAvailability.gameid == Channel.gameid).\
                            join(Game,Channel.gameid == Game.gameid).\
                            join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                            join(Pokemon,PokemonGameAvailability.pokemonid == Pokemon.pokemonid).\
                            join(PokemonNickname,Pokemon.pokemonid == PokemonNickname.pokemonid,isouter=True).\
                            filter(PokemonGameAvailability.pokemonavailabilitytypeid != 18,Channel.twitchuserid == twitchuserid).\
                            order_by(monShtein).first()
        #print(monName)
        Type1 = aliased(Type)
        Type2 = aliased(Type)
        monsel = [Pokemon.pokemonpokedexnumber,
                    Pokemon.pokemonname,
                    Pokemon.pokemoncapturerate,
                    LevelingRate.levelingratename
                ]                
        dex,name,capture,leveling = session.query(*monsel).\
                                select_from(Pokemon).\
                                join(PokemonNickname,Pokemon.pokemonid == PokemonNickname.pokemonid,isouter=True).\
                                join(LevelingRate,Pokemon.levelingrateid == LevelingRate.levelingrateid).\
                                filter(Pokemon.pokemonid == monid).\
                                first()
    finally:
        session.close()
    moveLevels = getLearnset(monName,namesFlag=False,twitchuserid=twitchuserid)
    evo = getEvos(monName,one=True)
    bst = getBST(monName)['message'].split('BST:')[1]
    typestring = getTypes(name)['message'].split('):')[1]
    message = "#"+str(dex).strip()+" "+name.strip()+" ("+gamegroupname.strip()+") | "+typestring.strip()+" | BST: "+str(bst).strip()+" | "+evo['message'].split('):')[1].strip()+" | "+str(leveling).strip()+" | "+moveLevels['message'].split(monName+":")[1].strip()
    # print(message)
    return {'message':message,'returnid':monid}
    
@app.route("/api/v2.0/move/<movename>")
def getMove(movename):
    session = Session(engine)
    twitchuserid = int(request.args.get("twitchuserid"))
    try:
        gamegroupname,generation = session.query(GameGroup.gamegroupname,GameGroup.generationid).\
                            select_from(Channel).\
                            join(Game,Channel.gameid == Game.gameid).\
                            join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                            filter(Channel.twitchuserid == twitchuserid).\
                            first()
        # print(gamegroupname)
        # print(generation)
        movesel = [Move.movename
                    ,GenerationMove.generationid
                    ,Type.typename
                    ,MoveCategory.movecategoryname
                    ,GenerationMove.movecontactflag
                    ,GenerationMove.movepp
                    ,GenerationMove.movepower
                    ,GenerationMove.moveaccuracy
                    ,GenerationMove.movepriority
                    ,GenerationMove.movedescription
                    ,Move.moveid]
        moveShtein = func.least(func.levenshtein(Move.movename,movename.title()),func.levenshtein(MoveNickname.movenickname,movename.title())).label("moveShtein")
        movename,gen,movetype,category,contactflag,pp,power,acc,priority,description,moveid = session.query(*movesel).select_from(GenerationMove).\
                                                                                    join(Move,GenerationMove.moveid == Move.moveid).\
                                                                                    join(MoveNickname,Move.moveid == MoveNickname.moveid,isouter=True).\
                                                                                    join(MoveCategory,GenerationMove.movecategoryid == MoveCategory.movecategoryid).\
                                                                                    join(Type,GenerationMove.typeid == Type.typeid).\
                                                                                    filter(GenerationMove.generationid <= generation).\
                                                                                    order_by(moveShtein,GenerationMove.generationid.desc()).\
                                                                                        first()
    finally:
        session.close()
    if contactflag == True:
        contact = "Contact"
    else:
        contact = "Non-Contact"
    message = str(movename)+" - Gen "+str(gen)+": ("+str(movetype)+", "+str(category)+", "+str(contact)+") | PP: "+str(pp)
    if power:
        message += " | Power: "+str(power)
    if acc:
        message += " | Acc: "+str(acc)
    message += " | Priority: "+str(priority)+" | Summary: "+description
    # print(message)
    return {'message':message,'returnid':moveid}
    
@app.route("/api/v2.0/nature/<naturename>")
def getNature(naturename):
    session = Session(engine)
    raisedStat,loweredStat = aliased(Stat),aliased(Stat)
    try:
        natureShtein = func.levenshtein(Nature.naturename,naturename).label("natureShtein")
        naturename,neutralflag,raisedstat,loweredstat,natureid = session.query(Nature.naturename,Nature.neutralnatureflag,raisedStat.statname,loweredStat.statname,Nature.natureid).\
                            select_from(Nature).\
                            join(raisedStat,Nature.raisedstatid == raisedStat.statid,isouter=True).\
                            join(loweredStat,Nature.loweredstatid == loweredStat.statid,isouter=True).\
                            order_by(natureShtein).first()
    finally:
        session.close()
    if neutralflag == True:
        message = naturename+" is a neutral nature."
    elif neutralflag == False:
        message = naturename+": +"+raisedstat+"/-"+loweredstat
    # print(message)
    return {'message':message,'returnid':natureid}

@app.route("/api/v2.0/pokecom/")
def getCommands():
    session = Session(engine)
    try:
        commands = session.query(Command.commandname).filter(Command.commandname != 'join').order_by(Command.commandname).all()
    finally:
            session.close()
    message = "Available commands: "
    for command in commands:
        message+= command[0]+", "
    message = message[0:len(command)-3]
    message += ". Use !help <command> for a description."
    # print(message)
    return {'message':message,'returnid':None}

@app.route("/api/v2.0/pokegame/<gamename>")
def updateGame(gamename):
    session = Session(engine)
    twitchuserid = int(request.args.get("twitchuserid"))
    gameShtein = func.least(func.levenshtein(Game.gamename,gamename),func.levenshtein(GameGroup.gamegroupabbreviation,gamename.upper())).label("gameShtein")
    try:
        gameid,gamename = session.query(Game.gameid,Game.gamename).join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).order_by(gameShtein).first()
        stmt = (update(Channel).where(Channel.twitchuserid == twitchuserid).values(gameid=gameid))
        session.execute(stmt)
        session.commit()
    finally:
        session.close()
    message = "Successfully changed the game to "+gamename+"."
    # print(message)
    return {'message':message,'returnid':gameid}
    
@app.route("/api/v2.0/pokeops/<operantlist>")
def insertOperant(operantlist):
    operantlist = operantlist.split(' ')
    if len(operantlist) < 1:
        return {'message':"This command requires at least one username to add to the user list.",'returnid':None}
    session = Session(engine)
    channeltwitchuserid = int(request.args.get("twitchuserid"))
    # print(channeltwitchuserid)
    newchannelperants = []
    newtwitchusers = []
    for operant in operantlist:
        print(operant)
        operanttwitchuserid = int(getTwitchID(operant))
        print(operanttwitchuserid)
        newtwitchusers.append({'twitchuserid':operanttwitchuserid,'twitchusername':operant})
        newchannelperants.append({"channeltwitchuserid":channeltwitchuserid,"operanttwitchuserid":operanttwitchuserid,"operanttypeid":2})
        print(newchannelperants)
    try:
        stmt = (insert(TwitchUser).values(newtwitchusers)).on_conflict_do_nothing(index_elements=['twitchuserid'])
        session.execute(stmt)
        session.commit()
    except:
        traceback.print_exc()
    finally:
        session.close()
    try:
        stmt = insert(ChannelOperant).values(newchannelperants)
        session.execute(stmt)
        session.commit()
    except:
        traceback.print_exc()
    finally:
        session.close()
    message = "Successfully added bot users to configuration."
    # print(message)
    return {'message':message,'returnid':None}

@app.route("/api/v2.0/revo/<parameters>")
def randoEvolution(parameters):
    session = Session(engine)
    twitchuserid = int(request.args.get("twitchuserid"))
    parameters = parameters.title().replace("Mime Jr","MimeJr")
    if len(parameters.split(" ")) == 1:
        monname = parameters
        limit = 10
    elif len(parameters.split(" ")) == 2:
        parameters = parameters.split(" ")
        try:
            monname = str(parameters[0])
            limit = int(parameters[1])
        except:
            monname = str(parameters[0])
            vanillaname = str(parameters[1])
            vanillaname = vanillaname.title()
            limit = 10
    elif len(parameters.split(" ")) > 2:
        parameters = parameters.split(" ")
        limit = int(parameters[len(parameters)-1])
        monname = str(parameters[0])
        vanillaname = str(parameters[1])
        vanillaname = vanillaname.title()
    monname = monname.title()
    multiFlag = 0
    try:
        monShtein = func.least(func.levenshtein(Pokemon.pokemonname,monname),
                            func.levenshtein(PokemonNickname.pokemonnickname,monname)).label("monShtein")
        monSel = [Pokemon.pokemonid
                ,Pokemon.pokemonname
                ,GameGroup.gamegroupid
                ,GameGroup.gamegroupname
                ,GameGroup.generationid
                ]
        monid,monName,gamegroup,gamegroupname,generation = session.query(*monSel).\
                                select_from(PokemonGameAvailability).\
                                join(Channel,PokemonGameAvailability.gameid == Channel.gameid).\
                                join(Game,Channel.gameid == Game.gameid).\
                                join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                                join(Pokemon,PokemonGameAvailability.pokemonid == Pokemon.pokemonid).\
                                join(PokemonNickname,Pokemon.pokemonid == PokemonNickname.pokemonid,isouter=True).\
                                filter(PokemonGameAvailability.pokemonavailabilitytypeid != 18,Channel.twitchuserid == twitchuserid).\
                                order_by(monShtein).first()
        monid,multiFlag = session.query(RandomizerEvolutionCounts.basepokemonid,func.count(func.distinct(RandomizerEvolutionCounts.vanillatargetid))).\
                                join(GameGroup,RandomizerEvolutionCounts.gamegroupid == GameGroup.gamegroupid).\
                                filter(RandomizerEvolutionCounts.basepokemonid == monid,GameGroup.generationid == generation).\
                                group_by(RandomizerEvolutionCounts.basepokemonid).\
                                first()
    except:
        session.rollback()
        traceback.print_exc()
        session.close()
        return {'message':"There was an error executing the revo command.",'returnid':monid}
    finally:
        session.close()
    if generation not in [1,2,3,4,5,6]:
        message = "This command is not yet implemented for games higher than generation 6."
        return {'message':message,'returnid':monid}
    if multiFlag > 1:
        try:
            # VanillaMon = aliased(Pokemon)
            monShtein = func.least(func.levenshtein(Pokemon.pokemonname,vanillaname),
                                func.levenshtein(PokemonNickname.pokemonnickname,vanillaname)).label("monShtein")
            vanillaid,vanillaName = session.query(Pokemon.pokemonid,Pokemon.pokemonname).\
                                    select_from(PokemonGameAvailability).\
                                    join(Channel,PokemonGameAvailability.gameid == Channel.gameid).\
                                    join(Game,Channel.gameid == Game.gameid).\
                                    join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                                    join(Pokemon,PokemonGameAvailability.pokemonid == Pokemon.pokemonid).\
                                    join(RandomizerEvolutionCounts,Pokemon.pokemonid == RandomizerEvolutionCounts.vanillatargetid).\
                                    join(PokemonNickname,Pokemon.pokemonid == PokemonNickname.pokemonid,isouter=True).\
                                    filter(Channel.twitchuserid == twitchuserid).\
                                    order_by(monShtein).first()
        except:
            message = 'Error: If your pokemon has multiple evolution methods, please pass the vanilla target evolution Pokemon as an additional paramater. (e.g. "!revo eevee vaporeon")'
            session.rollback()
            traceback.print_exc()
            session.close()
            return {'message':message,'returnid':monid}
        finally:
            session.close()
    evoList = [ RandomizerEvolutionCounts.basepokemonid
                            ,Pokemon.pokemonname
                            ,func.sum(RandomizerEvolutionCounts.seedcount)
                            ]
    try:
        randopercents = session.query(*evoList).select_from(RandomizerEvolutionCounts).\
                join(Pokemon,RandomizerEvolutionCounts.targetpokemonid == Pokemon.pokemonid).\
                join(GameGroup,RandomizerEvolutionCounts.gamegroupid == GameGroup.gamegroupid)
        if multiFlag > 1:
            randopercents = randopercents.filter(RandomizerEvolutionCounts.basepokemonid == monid,RandomizerEvolutionCounts.vanillatargetid == vanillaid,GameGroup.generationid == generation).\
                    group_by(RandomizerEvolutionCounts.basepokemonid,Pokemon.pokemonname).\
                    order_by(func.sum(RandomizerEvolutionCounts.seedcount).desc())
        else:
            randopercents = randopercents.filter(RandomizerEvolutionCounts.basepokemonid == monid,GameGroup.generationid == generation).\
                    group_by(RandomizerEvolutionCounts.basepokemonid,Pokemon.pokemonname)
            randopercents = randopercents.order_by(func.sum(RandomizerEvolutionCounts.seedcount).desc())
        # print(randopercents)
        randopercents = randopercents.limit(limit)
        denominator = session.query(func.sum(RandomizerEvolutionCounts.seedcount)).\
                        join(GameGroup,RandomizerEvolutionCounts.gamegroupid == GameGroup.gamegroupid).\
                        filter(RandomizerEvolutionCounts.basepokemonid == 2,GameGroup.generationid == generation).\
                        scalar()/100
    except:
        session.rollback()
        traceback.print_exc()
        session.close()
        return {'message':"There was an error executing the revo command.",'returnid':monid}
    finally:
        session.close()
    if len(randopercents.all()) == 0:
        message = monName+" does not evolve."
    else:
        if limit > randopercents.count():
            limit = randopercents.count()
        message = monName
        if multiFlag > 1:
            message+=" -> "+vanillaName
        message+=" Evos - Top "+str(limit)+" "
        monList = ""
        cumulativepercent = 0
        for basemonid,targetMon,targetCount in randopercents:
            percentchance = float(targetCount)/denominator
            cumulativepercent+= percentchance
            if round(percentchance,1) == 0:
                percentstr = "<0.1"
            else:
                percentstr = str(round(percentchance,1))
            monList+= targetMon+"("+percentstr+"%), "
        message+="("+str(round(cumulativepercent,1))+"%): "
        message+=monList[0:len(monList)-2]
    return {'message':message,'returnid':monid}

@app.route("/api/v2.0/revorev/<parameters>")
def randoEvolutionLookup(parameters):
    session = Session(engine)
    twitchuserid = int(request.args.get("twitchuserid"))
    if len(parameters.split(" ")) == 1:
        monname = parameters
        limit = 10
    elif len(parameters.split(" ")) == 2:
        parameters = parameters.split(" ")
        try:
            monname = str(parameters[0])
            limit = int(parameters[1])
        except:
            monname = str(parameters[0])
            vanillaname = str(parameters[1])
            vanillaname = vanillaname.title()
            limit = 10
    elif len(parameters.split(" ")) > 2:
        parameters = parameters.split(" ")
        limit = int(parameters[len(parameters)-1])
        monname = str(parameters[0])
        vanillaname = str(parameters[1])
        vanillaname = vanillaname.title()
    monname = monname.title()
    try:
        monShtein = func.least(func.levenshtein(Pokemon.pokemonname,monname),
                            func.levenshtein(PokemonNickname.pokemonnickname,monname)).label("monShtein")
        monSel = [Pokemon.pokemonid
                ,Pokemon.pokemonname
                ,GameGroup.gamegroupid
                ,GameGroup.gamegroupname
                ,GameGroup.generationid
                ]
        monid,monName,gamegroup,gamegroupname,generation = session.query(*monSel).\
                                select_from(PokemonGameAvailability).\
                                join(Channel,PokemonGameAvailability.gameid == Channel.gameid).\
                                join(Game,Channel.gameid == Game.gameid).\
                                join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                                join(Pokemon,PokemonGameAvailability.pokemonid == Pokemon.pokemonid).\
                                join(PokemonNickname,Pokemon.pokemonid == PokemonNickname.pokemonid,isouter=True).\
                                join(RandomizerEvolutionCounts,Pokemon.pokemonid == RandomizerEvolutionCounts.targetpokemonid).\
                                filter(PokemonGameAvailability.pokemonavailabilitytypeid != 18,Channel.twitchuserid == twitchuserid).\
                                order_by(monShtein).first()
    except:
        session.rollback()
        traceback.print_exc()
    finally:
        session.close()
    if generation not in [1,2,3,4,5]:
        message = "This command is not yet implemented for games higher than generation 4."
        return {'message':message,'returnid':monid}
    BasePokemon = aliased(Pokemon)
    VanillaPokemon = aliased(Pokemon)
    evoList = [ BasePokemon.pokemonname
                ,VanillaPokemon.pokemonname
                ,RandomizerEvolutionCounts.seedcount
                ]
    try:
        randopercents = session.query(*evoList).select_from(RandomizerEvolutionCounts).\
                join(VanillaPokemon,RandomizerEvolutionCounts.vanillatargetid == VanillaPokemon.pokemonid,isouter=True).\
                join(BasePokemon,RandomizerEvolutionCounts.basepokemonid == BasePokemon.pokemonid).\
                join(GameGroup,RandomizerEvolutionCounts.gamegroupid == GameGroup.gamegroupid).\
                filter(RandomizerEvolutionCounts.targetpokemonid == monid,GameGroup.generationid == generation).\
                order_by(RandomizerEvolutionCounts.seedcount.desc()).limit(limit)
        denominator = session.query(func.sum(RandomizerEvolutionCounts.seedcount)).\
                join(GameGroup,RandomizerEvolutionCounts.gamegroupid == GameGroup.gamegroupid).\
                filter(RandomizerEvolutionCounts.basepokemonid == 2,GameGroup.generationid == generation).\
                scalar()/100
    except:
        session.rollback()
        traceback.print_exc()
        session.close()
        return {'message':"There was an error executing the revo command.",'returnid':None}
    finally:
        session.close()
    if len(randopercents.all()) == 0:
        message = "Nothing evolves into "+monName+" in the randomizer - sorry!"
    else:
        try:
            if limit > randopercents.count():
                limit = randopercents.count()
            message = monName
            message+= " - Randomizer Base Evos (Top "+str(limit)+") - "
            monList = ""
            for basemon,vanillamon,targetCount in randopercents:
                percentchance = float(targetCount)/denominator
                if round(percentchance,1) == 0:
                    percentstr = "<0.1"
                else:
                    percentstr = str(round(percentchance,1))
                if vanillamon:
                    basemon = basemon+"->"+vanillamon
                monList+= basemon+"("+percentstr+"%), "
            message+=monList[0:len(monList)-2]
        except:
            traceback.print_exc()
            return {'message':"There was an error executing the revo command.",'returnid':None}
    return {'message':message,'returnid':monid}

@app.route("/api/v2.0/removeops/<removelist>")
def removeOperant(removelist):
    removelist = removelist.split(' ')
    session = Session(engine)
    channeltwitchuserid = int(request.args.get("twitchuserid"))
    removeoperants = []
    for removal in removelist:
        operanttwitchuserid = getTwitchID(removal)
        try:
            stmt = (delete(ChannelOperant).where(ChannelOperant.channeltwitchuserid==channeltwitchuserid,ChannelOperant.operanttwitchuserid==operanttwitchuserid))
            session.execute(stmt)
            session.commit()
        except:
            traceback.print_exc()
            session.rollback()
            return {'message':"There was an error executing the removeops command.",'returnid':None}
        finally:
            session.close()
    session.close()
    message = "Successfully removed bot users from configuration."
    # print(message)
    return {'message':message,'returnid':None}

def getTwitchID(username):
    file = 'chatbot.ini'
    config.read(file)
    idsecret = config['idfetch']['secret']
    idclient = config['idfetch']['clientid']
    authURL = 'https://id.twitch.tv/oauth2/token'
    AutParams = {'client_id': idclient,
             'client_secret': idsecret,
             'grant_type': 'client_credentials'
             }
    AutCall = requests.post(url=authURL, params=AutParams)
    access_token = AutCall.json()['access_token']
    url = 'https://api.twitch.tv/helix/users?login='+username
    headers = {
        'Authorization':"Bearer " + access_token,
        'Client-Id':idclient
    }
    response = requests.get(url,headers=headers)
    response.json()['data'][0]['id']
    userid = response.json()['data'][0]['id']
    # print(userid)
    return userid

@app.route("/api/v2.0/basestats/<monname>")
def getStats(monname):
    session = Session(engine)
    twitchuserid = int(request.args.get("twitchuserid"))
    monShtein = func.least(func.levenshtein(Pokemon.pokemonname,monname.title()),func.levenshtein(PokemonNickname.pokemonnickname,monname.title())).label("monShtein")
    try:
        monid,monName,gamegroup,gamegroupname,generation = session.query(Pokemon.pokemonid,Pokemon.pokemonname,GameGroup.gamegroupid,GameGroup.gamegroupname,GameGroup.generationid).\
                        select_from(PokemonGameAvailability).\
                        join(Channel,PokemonGameAvailability.gameid == Channel.gameid).\
                        join(Game,Channel.gameid == Game.gameid).\
                        join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                        join(Pokemon,PokemonGameAvailability.pokemonid == Pokemon.pokemonid).\
                        join(PokemonNickname,Pokemon.pokemonid == PokemonNickname.pokemonid,isouter=True).\
                        filter(PokemonGameAvailability.pokemonavailabilitytypeid != 18,Channel.twitchuserid == twitchuserid).\
                        order_by(monShtein).first()
    except:
        traceback.print_exc()
        session.close()
        return {'message':'There was an error with the basestats command.','returnid':None}
    try:
        monid,maxgen = session.query(PokemonStat.pokemonid,func.max(PokemonStat.generationid)).select_from(PokemonStat).\
                    filter(PokemonStat.generationid <= generation,PokemonStat.pokemonid == monid).group_by(PokemonStat.pokemonid).first()
        stats = session.query(Stat.statabbreviation,PokemonStat.pokemonstatvalue).select_from(PokemonStat).\
                    join(Stat, PokemonStat.statid == Stat.statid).\
                    filter(PokemonStat.pokemonid == monid,PokemonStat.generationid == maxgen).\
                    order_by(PokemonStat.generationid.desc()).\
                        all()
    except:
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
    message = monName+" (Gen "+str(generation)+"): "
    for statabb,statvalue in stats:
        message += "["+str(statabb) + " "+str(statvalue)+"] - "
    message = message[0:len(message)-2]
    return {'message':message,'returnid':monid}

@app.route("/api/v2.0/type/<monname>")
def getTypes(monname):
    session = Session(engine)
    twitchuserid = int(request.args.get("twitchuserid"))
    monShtein = func.least(func.levenshtein(Pokemon.pokemonname,monname.title()),func.levenshtein(PokemonNickname.pokemonnickname,monname.title())).label("monShtein")
    try:
        monid,monName,gamegroup,gamegroupname,generation = session.query(Pokemon.pokemonid,Pokemon.pokemonname,GameGroup.gamegroupid,GameGroup.gamegroupname,GameGroup.generationid).\
                        select_from(PokemonGameAvailability).\
                        join(Channel,PokemonGameAvailability.gameid == Channel.gameid).\
                        join(Game,Channel.gameid == Game.gameid).\
                        join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                        join(Pokemon,PokemonGameAvailability.pokemonid == Pokemon.pokemonid).\
                        join(PokemonNickname,Pokemon.pokemonid == PokemonNickname.pokemonid,isouter=True).\
                        filter(PokemonGameAvailability.pokemonavailabilitytypeid != 18,Channel.twitchuserid == twitchuserid).\
                        order_by(monShtein).first()
        type1name = session.query(Type.typename).\
                    select_from(PokemonType).\
                    join(Type).\
                    filter(PokemonType.pokemontypeorder == 1,PokemonType.pokemonid == monid,PokemonType.generationid <= generation).\
                    order_by(PokemonType.generationid.desc()).first()[0]
        type2name = session.query(Type.typename).\
                    select_from(PokemonType).\
                    join(Type).\
                    filter(PokemonType.pokemontypeorder == 2,PokemonType.pokemonid == monid,PokemonType.generationid <= generation).\
                    order_by(PokemonType.generationid.desc()).first()
    except:
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
    if type2name == None:
        message = monName+" (Gen "+str(generation)+"): "+type1name
    else:
        type2name = type2name[0]
        message = monName+" (Gen "+str(generation)+"): "+type1name+"/"+type2name
    # print(message)
    return {'message':message,'returnid':monid}
      
@app.route("/api/v2.0/weak/<monname>")
def getWeaknesses(monname):
    session = Session(engine)
    twitchuserid = int(request.args.get("twitchuserid"))
    try:
        monShtein = func.least(func.levenshtein(Pokemon.pokemonname,monname.title()),func.levenshtein(PokemonNickname.pokemonnickname,monname.title())).label("monShtein")
        monid,monName,gamegroup,gamegroupname,generation = session.query(Pokemon.pokemonid,Pokemon.pokemonname,GameGroup.gamegroupid,GameGroup.gamegroupname,GameGroup.generationid).\
                        select_from(PokemonGameAvailability).\
                        join(Channel,PokemonGameAvailability.gameid == Channel.gameid).\
                        join(Game,Channel.gameid == Game.gameid).\
                        join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                        join(Pokemon,PokemonGameAvailability.pokemonid == Pokemon.pokemonid).\
                        join(PokemonNickname,Pokemon.pokemonid == PokemonNickname.pokemonid,isouter=True).\
                        filter(PokemonGameAvailability.pokemonavailabilitytypeid != 18,Channel.twitchuserid == twitchuserid).\
                        order_by(monShtein).first()
    except:
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
    try:
        type1id,type1name = session.query(Type.typeid,Type.typename).\
                    select_from(PokemonType).\
                    join(Type).\
                    filter(PokemonType.pokemontypeorder == 1,PokemonType.pokemonid == monid,PokemonType.generationid <= generation).\
                    order_by(PokemonType.generationid.desc()).first()
        type2 = session.query(Type.typeid,Type.typename).\
                    select_from(PokemonType).\
                    join(Type).\
                    filter(PokemonType.pokemontypeorder == 2,PokemonType.pokemonid == monid,PokemonType.generationid <= generation).\
                    order_by(PokemonType.generationid.desc()).first()
        attackingType = aliased(Type)
        if type2:
            type2id,type2name = type2
            modifier2 = session.query(TypeMatchup.damagemodifier.label('dmgmodifier'),attackingType.typeid.label('typeid')).\
                select_from(TypeMatchup).\
                join(attackingType,(TypeMatchup.attackingtypeid == attackingType.typeid) & (attackingType.generationid <= generation)).\
                filter(TypeMatchup.generationid == generation,TypeMatchup.defendingtypeid == type2id).\
                    distinct(attackingType.typename).subquery()
            modifier1 = session.query(TypeMatchup.damagemodifier.label('dmgmodifier'),attackingType.typeid.label('typeid')).\
                select_from(TypeMatchup).\
                join(attackingType,(TypeMatchup.attackingtypeid == attackingType.typeid) & (attackingType.generationid <= generation)).\
                filter(TypeMatchup.generationid == generation,TypeMatchup.defendingtypeid == type1id).\
                    distinct(attackingType.typename).subquery()
            modifiers = session.query((modifier2.c.dmgmodifier*modifier1.c.dmgmodifier).label('dmgmodifier'),modifier2.c.typeid).\
                select_from(modifier1).join(modifier2,modifier1.c.typeid == modifier2.c.typeid).subquery()
        else:
            type2id = None
            modifiers = session.query(TypeMatchup.damagemodifier.label('dmgmodifier'),attackingType.typeid.label('typeid')).\
                select_from(TypeMatchup).\
                join(attackingType,(TypeMatchup.attackingtypeid == attackingType.typeid) & (attackingType.generationid <= generation)).\
                filter(TypeMatchup.generationid == generation,TypeMatchup.defendingtypeid == type1id).\
                    subquery()
        modifiersfinal = session.query(modifiers.c.dmgmodifier,func.string_agg(attackingType.typename,aggregate_order_by((", "),attackingType.typename))).\
                join(attackingType,modifiers.c.typeid == attackingType.typeid).\
                group_by(modifiers.c.dmgmodifier).all()
    except:
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
    message = monName+" ("+type1name
    if type2:
        message += "/"+type2name
    message += "), Gen "+str(generation)+" = "
    for modifier,typelist in modifiersfinal:
        message+= "["+(str(modifier)+"x").replace("0.25x","¼").replace("0.50x","½").replace("0.5x","½").replace("0.00","0").replace("0.0","0").replace(".00","").replace(".0","")+": "+typelist+"] - "
    message = message[0:len(message)-2]
    # print(message)
    return {'message':message,'returnid':monid}
    
@app.route("/api/v2.0/xp/<parameters>")
def getXP(parameters):
    session = Session(engine)
    twitchuserid = int(request.args.get("twitchuserid"))
    if len(parameters.split(" ")) == 1:
        monname = parameters
        enemylevel = 8
        monLevel = None
    elif len(parameters.split(" ")) == 2:
        parameters = parameters.split(" ")
        try:
            monname = str(parameters[1])
            enemylevel = int(parameters[0])
        except:
            monname = str(parameters[0])
            enemylevel = int(parameters[1])
        monlevel = None
    elif len(parameters.split(" ")) > 2:
        parameters = parameters.split(" ")
        try:
            enemylevel = int(parameters[0])
            monlevel = int(parameters[1])
            monname = str(parameters[2:])
        except:
            try:
                enemylevel = int(parameters[0])
                monname = str(parameters[1:])
                monlevel = None
            except:
                enemylevel = int(parameters[len(parameters)-1])
                monname = str(parameters[0:len(parameters)-1])
                monlevel = None
    session = Session(engine)
    try:
        monShtein = func.least(func.levenshtein(Pokemon.pokemonname,monname.title()),func.levenshtein(PokemonNickname.pokemonnickname,monname.title())).label("monShtein")
        monid,monName,gamegroup,gamegroupabbr,generation = session.query(Pokemon.pokemonid,Pokemon.pokemonname,GameGroup.gamegroupid,GameGroup.gamegroupabbreviation,GameGroup.generationid).\
                        select_from(PokemonGameAvailability).\
                        join(Channel,PokemonGameAvailability.gameid == Channel.gameid).\
                        join(Game,Channel.gameid == Game.gameid).\
                        join(GameGroup,Game.gamegroupid == GameGroup.gamegroupid).\
                        join(Pokemon,PokemonGameAvailability.pokemonid == Pokemon.pokemonid).\
                        join(PokemonNickname,Pokemon.pokemonid == PokemonNickname.pokemonid,isouter=True).\
                        filter(PokemonGameAvailability.pokemonavailabilitytypeid != 18,Channel.twitchuserid == twitchuserid).\
                        order_by(monShtein).first()
    except:
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
    if enemylevel > 100:
        return {"message":"Max level for the !xp command is 100. Adjust the level and try again.",'returnid':monid}
    try:
        monyield, monName, monid = session.query(PokemonExperienceYield.experienceyieldvalue,Pokemon.pokemonname,Pokemon.pokemonid).\
                        select_from(PokemonExperienceYield).\
                        join(Pokemon,PokemonExperienceYield.pokemonid == Pokemon.pokemonid).\
                        filter(PokemonExperienceYield.generationid <= generation,PokemonExperienceYield.pokemonid == monid).order_by(PokemonExperienceYield.generationid.desc()).\
                            first()
    except:
        session.rollback()
        traceback.print_exc()
    finally:
        session.close()
    monyield = float(monyield)
    a = 1
    b = monyield
    L = enemylevel
    L2 = enemylevel if monlevel is None else monlevel
    s = 1
    if generation != 5 and generation != 7:
        wildxp = str(int(math.floor(b*a*L/7)))
        a = 1.5
        trainerxp = str(int(math.floor(float(wildxp)*1.5)))
    elif generation == 5:
        wildxp = str(int(math.floor((1*monyield*enemylevel/5)*math.pow((2*enemylevel+10)/(enemylevel+monlevel+10),2.5))+1))
        a = 1.5
        trainerxp = str(int(math.floor((1.5*monyield*enemylevel/5)*math.pow((2*enemylevel+10)/(enemylevel+monlevel+10),2.5))+1))
    elif generation == 7:
        monEvo = getEvos(parameters)
        try:
            evoLevel = monEvo[0][1]
        except:
            evoLevel = L2+1
        if int(L2) >= int(evoLevel):
            v = 1.2
        else:
            v = 1
        wildxp = str(int(math.floor((b*L*v/5*s)*(math.pow((2*L+10)/(L+L2+10),2.5)))))
        trainerxp = str(int(math.floor((b*L*v/5*s)*(math.pow((2*L+10)/(L+L2+10),2.5)))))
    message = monName+" Lvl "+str(enemylevel)+" XP ("+gamegroupabbr+"): Wild="+wildxp+"/Trainer="+trainerxp
    # print(message)
    return {'message':message,'returnid':monid}      

#######################
### OTHER FUNCTIONS ###
#######################

if __name__ == '__main__':
    app.run()