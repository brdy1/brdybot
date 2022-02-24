from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse, request
from numpy.lib.type_check import typename
from sqlalchemy import Column, Table, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import alias
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, insert,update,delete
from sqlalchemy.sql.schema import PrimaryKeyConstraint
from werkzeug.routing import BaseConverter
from pprint import pprint
from brdybot import *
from schema import *
import configparser
import pandas as pd

config = configparser.ConfigParser()
file = "chatbot.ini"
config.read(file)
host = config['database']['host']
database = config['database']['database']
user = config['database']['user']
password = config['database']['password']

#################################################
class TypeListConverter(BaseConverter):
    """Match ints separated with ';'."""

    # at least one int, separated by ;, with optional trailing ;
    regex = r'\d+(?:;\d+)*;?'

    # this is used to parse the url and pass the list to the view function
    def to_python(self, value):
        return [str(x) for x in value.split(';')]

    # this is used when building a url with url_for
    def to_url(self, value):
        return ';'.join(str(x) for x in value)


#################################################
# Flask Setup
#################################################
app = Flask(__name__)
app.url_map.converters['type_list'] = TypeListConverter

api = Api(app)

#################################################
# App Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/pokemon<br/>"
        f"/api/v1.0/ability<br/>"
        f"/api/v1.0/move<br/>"
        f"/api/v1.0/coverage"
    )

@app.route("/api/v1.0/pokemon")
def pokemon():
    monName = request.args.get("name")
    if monName:
        monName = monName.title().replace("'","''")
    monID = request.args.get("id")
    monDex = request.args.get("dex")
    reqGeneration = request.args.get("gen")

    # Create our session (link) from Python to the DB
    session = Session(engine)
    """Return a list of all pokemon names"""
    monsel = [ Pokemon.pokemonid,
            Pokemon.pokemonname,
            Pokemon.pokemonpokedexnumber,
            Pokemon.pokemoncapturerate,
            Pokemon.pokemonlegendaryflag,
            Pokemon.pokemonmythicflag,
            ]
    # Query all pokemon
    if monName:
        pokemonNames =  session.query(*monsel).\
                        order_by(func.levenshtein(Pokemon.pokemonname, monName),
                        Pokemon.pokemonpokedexnumber,
                        Pokemon.pokemonsuffix).first()
    elif monDex:
        pokemonNames =  session.query(*monsel).\
                        filter(Pokemon.pokemonpokedexnumber == monDex).\
                        order_by(Pokemon.pokemonpokedexnumber,
                        Pokemon.pokemonsuffix).first()
    elif monID:
        pokemonNames = session.query(*monsel).\
                        filter(Pokemon.pokemonid == monID).\
                        order_by(Pokemon.pokemonpokedexnumber,
                        Pokemon.pokemonsuffix).first()
    pokemon = {}
    monid,monName,dex,catchrate,legendary,mythic = pokemonNames
    # Define a select statement for the stat query
    statsel = [ Stat.statname,
                    Stat.statid,
                    PokemonStat.pokemonstatvalue,
                    PokemonStat.generationid,
                    ]
    # Fetch the stats for the pokemon
    stats = session.query(*statsel).\
                        join(Stat,PokemonStat.statid == Stat.statid).\
                        join(Pokemon,PokemonStat.pokemonid == Pokemon.pokemonid).\
                        filter(PokemonStat.pokemonid == monid).all()

    statGens = session.query(PokemonStat.generationid).filter(PokemonStat.pokemonid == monid).distinct(PokemonStat.generationid).all()
    # Create a blank list to store the pokemon's stats for each generation
    # Create a blank dictionary
    monStats = {}
    # For each set of stats in a record
    for gen in statGens:
        gen = int(gen[0])
        # Create a blank dictionary for the gen
        monStats[gen] = {}
    # For each stat for a gen
    for statname,statid,statvalue,statgen in stats:
        # Assign it to the correct dict value
        monStats[int(statgen)][statname] = statvalue

    # Define a select statement for the move query


    gamegroups = session.query(GameGroup.gamegroupname).\
                    join(PokemonMove,GameGroup.gamegroupid == PokemonMove.gamegroupid).\
                        filter(PokemonMove.pokemonid == monid).distinct(GameGroup.gamegroupname).all()
    ggList = {}
    for gamegroup in gamegroups:
        gamegroup=gamegroup[0]
        ggList[gamegroup] = {}

    movemethods = session.query(PokemonMove.pokemonmoveid,PokemonMoveMethod.pokemonmovemethodname,GameGroup.gamegroupname).\
                    join(PokemonMoveMethod,PokemonMove.pokemonmovemethodid == PokemonMoveMethod.pokemonmovemethodid).\
                    join(GameGroup,PokemonMove.gamegroupid == GameGroup.gamegroupid).\
                        filter(PokemonMove.pokemonid == monid).distinct(GameGroup.gamegroupname,PokemonMoveMethod.pokemonmovemethodname).all()

    for pokemonid,method,gamegroup in movemethods:
        if method == 'Level up':
            ggList[gamegroup][method] = {}

    movesel = [ PokemonMove.pokemonmoveid,
                PokemonMove.pokemonmovelevel,
                Move.moveid,
                Move.movename,
                PokemonMoveMethod.pokemonmovemethodname,
                GameGroup.gamegroupname
                ]

    moves = session.query(*movesel).\
            join(Move,PokemonMove.moveid == Move.moveid).\
            join(PokemonMoveMethod,PokemonMove.pokemonmovemethodid == PokemonMoveMethod.pokemonmovemethodid).\
            join(GameGroup,PokemonMove.gamegroupid == GameGroup.gamegroupid).\
                filter(PokemonMove.pokemonid == monid).all()

    for monmoveid,movelevel,moveid,movename,movemethod,gamegroup in moves:
        if movemethod == 'Level up':
            ggList[gamegroup][movemethod][str(movelevel)] = movename
        # elif movemethod == 'Tutor' or movemethod == 'Egg' or movemethod == 'Machine':
        #     print(str(monmoveid)+" "+str(movelevel)+" "+str(moveid)+" "+str(movename)+" "+str(movemethod)+" "+str(gamegroup))
        #     if movename not in ggList[gamegroup][method]:
        #         ggList[gamegroup][method] = [movename]  # <-- Change this line
        #     else:
        #         ggList[gamegroup][method].append(movename)

    # Define a select statement for the evolution query
    evosel = [ PokemonEvolution.pokemonevolutionid,
            PokemonEvolution.basepokemonid,
            Pokemon.pokemonname,
            Item.itemname,
            PokemonEvolutionLevel.pokemonevolutionlevel,
            Location.locationname,
            Move.movename,
            PokemonEvolutionString.pokemonevolutionstring,
            PokemonEvolution.gamegroupid
            ]

    # Fetch the evolution information for the pokemon as base mon
    evos = session.query(*evosel).\
            join(PokemonEvolutionItem, isouter=True).\
            join(Item,PokemonEvolutionItem.itemid == Item.itemid, isouter=True).\
            join(PokemonEvolutionLevel, isouter=True).\
            join(PokemonEvolutionLocation, isouter=True).\
            join(Location,PokemonEvolutionLocation.locationid == Location.locationid, isouter=True).\
            join(PokemonEvolutionMove, isouter=True).\
            join(Move,PokemonEvolutionMove.moveid == Move.moveid, isouter=True).\
            join(PokemonEvolutionString, isouter=True).\
            join(Pokemon,PokemonEvolution.targetpokemonid == Pokemon.pokemonid).\
                filter(PokemonEvolution.basepokemonid == monid).all()

    evoList = {}
    for evo in evos:
        evoid,baseid,targetname,item,level,location,move,string,ggid = evo

        monEvo = {
            "item":item,
            "level":level,
            "location":location,
            "move":move,
            "string":string
        }
        
        evoList[targetname] = monEvo
    montypes = pd.read_sql("SELECT pt.generationid,t.typename FROM pokemon.pokemontype pt LEFT JOIN pokemon.type t ON pt.typeid = t.typeid WHERE pt.pokemonid = (SELECT pokemonid FROM pokemon.pokemon WHERE pokemonname = '"+monName.replace("'","''")+"')",engine)
    typetable = pd.crosstab([montypes.generationid],montypes.typename)
    typeDict = typetable.to_dict()
    for key in typeDict.keys():
        for gen in typeDict[key]:
            print("Gen: "+str(gen))
            print("Key: "+str(key))
            print(typeDict[key][gen])
            if typeDict[key][gen] == 0:
                typeDict[key][gen] = False
            else:
                typeDict[key][gen] = True

    monDict = {
        "dex": dex,
        "evolutions": evoList,
        "catch rate": catchrate,
        "legendary": legendary,
        "mythic": mythic,
        "stats": monStats,
        "moves": ggList,
        "types": typeDict
    }
    
    pokemon[monID] = monDict
    session.close()
    return jsonify(pokemon)

@app.route("/api/v1.0/move")
def move():
    moveName = request.args.get("name")
    # Create our session (link) from Python to the DB
    session = Session(engine)
    """Return a list of move data including the type, power, priority, pp, and contact information of each move"""
    # Define a a list of columns for the select statement in the loop below
    sel = [ Move.movename,
            Type.typename,
            GenerationMove.movepower,
            GenerationMove.movepriority,
            GenerationMove.moveaccuracy,
            MoveCategory.movecategoryname,
            GenerationMove.movepp,
            GenerationMove.movedescription,
            GenerationMove.movecontactflag,
            GenerationMove.generationid
            ]
    # Query for all move names
    names = session.query(Move.movename).order_by(func.levenshtein(Move.movename, moveName)).first()
    name = names[0]
    # Create a blank 'primary' move dictionary with a blank list of move names
    moves = {}
    moves[name] = {}
    # Fetch the generationmove records
    results = session.query(*sel).\
                join(Move, GenerationMove.moveid==Move.moveid).\
                join(Type, GenerationMove.typeid==Type.typeid).\
                join(MoveCategory, GenerationMove.movecategoryid == MoveCategory.movecategoryid).\
                filter(Move.movename == name).all()
    for genName,type,power,priority,accuracy,category,pp,description,contact,generation in results:
        genMove = {
            "type": type,
            "power": power,
            "priority": priority,
            "accuracy": accuracy,
            "pp": pp,
            "description": description,
            "contact": contact,
            "category": category
        }
        moves[name][generation] = genMove
    session.close()
    return jsonify(moves)

@app.route("/api/v1.0/weakness")
def weakness():
    monID = request.args.get("id")
    gen = request.args.get("gen")
    channel = request.args.get("channel")
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
    return jsonify(printableDict)

@app.route("/api/v1.0/coverage/<type_list:types>")
def apiCoverage(types):
    session = Session(engine)
    typeIDs = []
    typeNames = []
    for coverageType in types:
        types[types.index(coverageType)] = str(coverageType)
    typeQuery = session.query(Type.typename,Type.typeid).filter(Type.typeid.in_(types)).all()
    for typeArray in typeQuery:
        typeIDs.append(typeArray[1])
        typeNames.append(typeArray[0])
    channel = request.args.get("channel")
    gameID = str(getGameID(channel))
    game = getGame(channel)
    gen = getGeneration(channel)
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
        coverageString += str(array[0]).replace(".0",".").replace("0.5",".5").replace("0.25",".25").replace("0.","0").replace("1.","1").replace("2.","2").replace("4.","4")+"x: "+str(array[1])
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
    if pokemonList[2][0] < 1:
        limit = limit+pokemonList[2][1]
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

@app.route("/api/v1.0/coverage2/<type_list:types>")
def coverage(types):
    session = Session(engine)
    typeIDs = []
    typeNames = []
    for coverageType in types:
        types[types.index(coverageType)] = str(coverageType)
    typeQuery = session.query(Type.typename,Type.typeid).filter(Type.typeid.in_(types)).all()
    for typeArray in typeQuery:
        typeIDs.append(typeArray[1])
        typeNames.append(typeArray[0])
    channel = request.args.get("channel")
    gameID = str(getGameID(channel))
    game = getGame(channel)
    gen = getGeneration(channel)
    montypes = pd.read_sql("SELECT pokemontype.generationid,typename FROM pokemon.pokemontype LEFT JOIN pokemon.pokemon ON pokemontype.pokemonid = pokemon.pokemonid LEFT JOIN pokemon.type ON pokemontype.typeid = type.typeid WHERE pokemon.pokemonname = '"+monName+"'",engine)
    montypes = pd.crosstab([montypes.generationid],montypes.typename)
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
        coverageString += str(array[0]).replace(".0",".").replace("0.5",".5").replace("0.25",".25").replace("0.","0").replace("1.","1").replace("2.","2").replace("4.","4")+"x: "+str(array[1])
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

# @app.route("/api/v1.0/bst")
# def move():
#     monID = request.args.get("id")
#     gen = request.args.get("gen")
#     session = Session(engine)
#     bstAl = session.query(func.sum(PokemonStat.pokemonstatvalue)).\
#                 filter(PokemonStat.pokemonid == monID,PokemonStat.generationid <= gen).\
#                 group_by(PokemonStat.generationid).\
#                 order_by(PokemonStat.generationid.desc()).\
#                     first()
#     monBST = str(bstAl[0])
#     return monBST

# @app.route("/api/v1.0/xp")
# def xp():
#     monID = request.args.get("id")
#     gen = request.args.get("gen")
#     enemylevel = request.args.get("enemylevel")
#     monlevel = request.args.get("monlevel")

#     enemylevel = float(enemylevel)
#     if monlevel == None:
#         monlevel = enemylevel
#     monlevel = float(monlevel)
#     gen = int(getGeneration(channel))
#     session = Session(engine)
#     try:
#         xpyieldAl = session.query(PokemonExperienceYield.experienceyieldvalue,PokemonExperienceYield.generationid).\
#                         filter(PokemonExperienceYield.pokemonid == int(monID), PokemonExperienceYield.generationid <= gen).\
#                         order_by(PokemonExperienceYield.generationid.desc()).\
#                             first()
#         print(xpyieldAl)
#         session.close()
#         monyield = float(xpyieldAl[0])
#         a = 1
#         b = monyield
#         L = enemylevel
#         L2 = monlevel
#         s = 1
#         if gen != 5 and gen != 7:
#             wildxp = str(int(math.floor(b*a*L/7)))
#             a = 1.5
#             trainerxp = str(int(math.floor(b*a*L/7)))
#         elif gen == 5:
#             wildxp = str(int(math.floor((1*monyield*enemylevel/5)*math.pow((2*enemylevel+10)/(enemylevel+monlevel+10),2.5))+1))
#             a = 1.5
#             trainerxp = str(int(math.floor((1.5*monyield*enemylevel/5)*math.pow((2*enemylevel+10)/(enemylevel+monlevel+10),2.5))+1))
#         elif gen == 7:
#             monEvo = getMonEvoArray(monID,channel)
#             try:
#                 evoLevel = monEvo[0][1]
#             except:
#                 evoLevel = L2+1
#             if int(L2) >= int(evoLevel):
#                 v = 1.2
#             else:
#                 v = 1
#             wildxp = str(int(math.floor((b*L*v/5*s)*(math.pow((2*L+10)/(L+L2+10),2.5)))))
#             trainerxp = str(int(math.floor((b*L*v/5*s)*(math.pow((2*L+10)/(L+L2+10),2.5)))))
#         return wildxp,trainerxp
#     except:
#         traceback.print_exc()
#         string='unknown'
#         return string,string



if __name__ == '__main__':
    app.run()