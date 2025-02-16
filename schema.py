from ast import For
from decimal import Decimal
from sqlalchemy import BigInteger, Column, Table, Integer, String, Boolean, DateTime, ForeignKey, DECIMAL
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
import configparser


config = configparser.ConfigParser()
file = "C:/Users/Administrator/brdybot/chatbot.ini"
config.read(file)
host = config['database']['host']
database = config['database']['database']
user = config['database']['user']
password = config['database']['password']

#################################################
# Database Setup
#################################################
dbschema='pokemon,bot,warehouse'
engine = create_engine('postgresql+psycopg2://'+user+':'+password+'@'+host+':5432/'+database,connect_args={'options': '-csearch_path={}'.format(dbschema)})
Base = declarative_base(engine)
    
class Ability(Base):
    __tablename__ = 'ability'
    abilityid = Column("abilityid",Integer,primary_key=True)
    abilityname = Column("abilityname",String(30))

class EvolutionType(Base):
    __tablename__ = 'evolutiontype'
    evolutiontypeid = Column("evolutiontypeid",Integer,primary_key=True)
    evolutiontypename = Column("evolutiontypename",String(50))
    evolutiontypedescription = Column("evolutiontypedescription",String(500))

class Game(Base):
    __tablename__ = 'game'
    gameid = Column("gameid",Integer,primary_key=True)
    gamename = Column("gamename",String(50))
    gamegroupid = Column("gamegroupid",Integer,ForeignKey("gamegroup.gamegroupid"))
    
class GameGroup(Base):
    __tablename__ = 'gamegroup'
    gamegroupid = Column("gamegroupid",Integer,primary_key=True)
    gamegroupname = Column("gamegroupname",String(30))
    gamegroupabbreviation = Column("gamegroupabbreviation",String(30))
    gamegrouporder = Column("gamegrouporder",Integer)
    generationid = Column("generationid", Integer, ForeignKey("generation.generationid"))
    
class Generation(Base):
    __tablename__ = 'generation'
    generationid = Column("generationid",Integer,primary_key=True)
    generationname = Column("generationname",String(50))
    
class GenerationAbility(Base):
    __tablename__ = 'generationability'
    generationabilityid = Column("generationabilityid",Integer,primary_key=True)
    abilityid = Column("abilityid",Integer,ForeignKey("ability.abilityid"))
    abilitydescription = Column("abilitydescription",String(500))
    generationid = Column("generationid",Integer,ForeignKey("generation.generationid"))

class GenerationMove(Base):
    __tablename__ = 'generationmove'
    generationmoveid = Column("generationmoveid",Integer,primary_key=True)
    movedescription = Column("movedescription",String(500))
    movecategoryid = Column("movecategoryid",Integer,ForeignKey("movecategory.movecategoryid"))
    movepriority = Column("movepriority",Integer)
    movepower = Column("movepower",Integer)
    movepp = Column("movepp",Integer)
    movecontactflag = Column("movecontactflag",Boolean)
    typeid = Column("typeid", Integer, ForeignKey("type.typeid"))
    generationid = Column("generationid", Integer,ForeignKey("generation.generationid"))
    moveaccuracy = Column("moveaccuracy",Integer)
    moveid = Column("moveid", Integer, ForeignKey("move.moveid"))

class Item(Base):
    __tablename__ = 'item'
    itemid = Column("itemid",Integer,primary_key=True)
    itemname = Column("itemname",String(50))

class LevelingRate(Base):
    __tablename__ = 'levelingrate'
    levelingrateid = Column("levelingrateid",Integer,primary_key=True)
    levelingratename = Column("levelingratename",String(30))

class LevelingRateLevelThreshold(Base):
    __tablename__ = 'levelingratelevelthreshold'
    levelingratethresholdid = Column('levelingratelevelthresholdid',Integer,primary_key=True)
    levelingrateid = Column('levelingrateid',Integer,ForeignKey('levelingrate.levelingrateid'))
    levelingratelevelthresholdlevel = Column('levelingratelevelthresholdlevel',Integer)
    levelingratelevelthresholdexperience = Column('levelingratelevelthresholdexperience',BigInteger)

class Location(Base):
    __tablename__ = 'location'
    locationid = Column("locationid",Integer,primary_key=True)
    locationname = Column("locationname",String(30))

class Move(Base):
    __tablename__ = 'move'
    moveid = Column("moveid",Integer,primary_key=True)
    movename = Column("movename",String(50))

class MoveCategory(Base):
    __tablename__ = 'movecategory'
    movecategoryid = Column("movecategoryid",Integer,primary_key=True)
    movecategoryname = Column("movecategoryname",String(50))

class MoveNickname(Base):
    __tablename__ = "movenickname"
    movenicknameid = Column("movenicknameid",Integer,primary_key=True)
    moveid = Column("moveid",Integer,ForeignKey("move.moveid"))
    movenickname = Column("movenickname",String(50))

class Nature(Base):
    __tablename__ = "nature"
    natureid = Column("natureid",Integer,primary_key=True)
    naturename = Column("naturename",String(20))
    neutralnatureflag = Column("neutralnatureflag",Boolean)
    raisedstatid = Column("raisedstatid",Integer,ForeignKey("stat.statid"))
    loweredstatid = Column("loweredstatid",Integer,ForeignKey("stat.statid"))

class Pokemon(Base):
    __tablename__ = 'pokemon'
    pokemonid = Column("pokemonid",Integer,primary_key=True)
    pokemonname =  Column("pokemonname",String(50))
    pokemoncapturerate = Column("pokemoncapturerate",Integer)
    levelingrateid = Column("levelingrateid",Integer,ForeignKey("levelingrate.levelingrateid"))
    pokemonpokedexnumber = Column("pokemonpokedexnumber",Integer)
    pokemonlegendaryflag = Column("pokemonlegendaryflag",Integer)
    pokemonmythicflag = Column("pokemonmythicflag",Integer)
    pokemonsuffix = Column("pokemonsuffix",String(15))
    pokemonspeciesname = Column("pokemonspeciesname",String(30))

class PokemonAvailabilityType(Base):
    __tablename__ = 'pokemonavailabilitytype'
    pokemonavailabilitytypeid = Column("pokemonavailabilitytypeid",Integer,primary_key=True)
    pokemonavailabilitytypename = Column("pokemonavailabilitytypename",String(50))
    pokemonavailabilitytypedescription = Column("pokemonavailabilitytypedescription",String(300))

class PokemonEvolution(Base):
    __tablename__ = 'pokemonevolution'
    pokemonevolutionid = Column("pokemonevolutionid",Integer,primary_key=True)
    evolutiontypeid = Column("evolutiontypeid",Integer,ForeignKey("evolutiontype.evolutiontypeid"))
    basepokemonid = Column("basepokemonid",Integer)
    targetpokemonid = Column("targetpokemonid",Integer)
    gamegroupid = Column("gamegroupid",Integer,ForeignKey("gamegroup.gamegroupid"))
    
class PokemonEvolutionInfo(Base):
    __tablename__ = 'pokemonevolutioninfo'
    pokemonevolutionid = Column("pokemonevolutionid",Integer,primary_key=True)
    evolutiontypeid = Column("evolutiontypeid",Integer,ForeignKey("evolutiontype.evolutiontypeid"))
    basepokemonid = Column("basepokemonid",Integer)
    targetpokemonid = Column("targetpokemonid",Integer)
    gamegroupid = Column("gamegroupid",Integer,ForeignKey("gamegroup.gamegroupid"))
    itemid = Column("itemid",Integer, ForeignKey("item.itemid"))
    pokemonevolutionlevel = Column("pokemonevolutionlevel",Integer)
    locationid = Column("locationid",Integer, ForeignKey("location.locationid"))
    moveid = Column("moveid",Integer, ForeignKey("move.moveid"))
    pokemonevolutionstring = Column("pokemonevolutionuniquestring",String(150))

class PokemonEvolutionItem(Base):
    __tablename__ = 'pokemonevolutionitem'
    pokemonevolutionid = Column("pokemonevolutionid",Integer, ForeignKey("pokemonevolution.pokemonevolutionid"), primary_key=True)
    itemid = Column("itemid",Integer)
    
class PokemonEvolutionLevel(Base):
    __tablename__ = 'pokemonevolutionlevel'
    pokemonevolutionid = Column("pokemonevolutionid",Integer, ForeignKey("pokemonevolution.pokemonevolutionid"),primary_key=True)
    pokemonevolutionlevel = Column("pokemonevolutionlevel",Integer)
    
class PokemonEvolutionLocation(Base):
    __tablename__ = 'pokemonevolutionlocation'
    pokemonevolutionid = Column("pokemonevolutionid",Integer, ForeignKey("pokemonevolution.pokemonevolutionid"),primary_key=True)
    locationid = Column("locationid",Integer)
    
class PokemonEvolutionMove(Base):
    __tablename__ = 'pokemonevolutionmove'
    pokemonevolutionid = Column("pokemonevolutionid",Integer, ForeignKey("pokemonevolution.pokemonevolutionid"),primary_key=True)
    moveid = Column("moveid",Integer)
    
class PokemonEvolutionString(Base):
    __tablename__ = 'pokemonevolutionstring'
    pokemonevolutionid = Column("pokemonevolutionid",Integer, ForeignKey("pokemonevolution.pokemonevolutionid"),primary_key=True)
    pokemonevolutionstring = Column("pokemonevolutionuniquestring",String(150))
    
class PokemonEvolutionType(Base):
    __tablename__ = 'pokemonevolutiontype'
    pokemonevolutionid = Column("pokemonevolutionid",Integer, ForeignKey("pokemonevolution.pokemonevolutionid"),primary_key=True)
    evolutiontypeid = Column("evolutiontypeid",Integer,primary_key=True)
    
class PokemonExperienceYield(Base):
    __tablename__ = 'pokemonexperienceyield'
    pokemonexperienceyieldid = Column("pokemonexperienceyieldid",Integer,primary_key=True)
    pokemonid = Column("pokemonid",Integer, ForeignKey("pokemon.pokemonid"))
    generationid = Column("generationid",Integer, ForeignKey("generation.generationid"))
    experienceyieldvalue = Column("experienceyieldvalue",Integer)
    
class PokemonGameAvailability(Base):
    __tablename__ = "pokemongameavailability"
    pokemongameavailabilityid = Column("pokemongameavailabilityid", primary_key=True)
    pokemonid = Column("pokemonid",Integer,ForeignKey("pokemon.pokemonid"))
    pokemonavailabilitytypeid = Column("pokemonavailabilitytypeid",Integer,ForeignKey("pokemonavailabilitytype.pokemonavailabilitytypeid"))
    gameid = Column("gameid",Integer,ForeignKey("game.gameid"))
    
class PokemonMove(Base):
    __tablename__ = 'pokemonmove'
    pokemonmoveid = Column("pokemonmoveid",Integer,primary_key=True)
    pokemonid = Column("pokemonid",Integer, ForeignKey("pokemon.pokemonid"))
    moveid = Column("moveid",Integer, ForeignKey("move.moveid"))
    pokemonmovelevel = Column("pokemonmovelevel",Integer)
    pokemonmovemethodid = Column("pokemonmovemethodid",Integer, ForeignKey("pokemonmovemethod.pokemonmovemethodid"))
    gamegroupid = Column("gamegroupid",Integer, ForeignKey("gamegroup.gamegroupid"))
    
class PokemonMoveMethod(Base):
    __tablename__ = 'pokemonmovemethod'
    pokemonmovemethodid = Column("pokemonmovemethodid",Integer,primary_key=True)
    pokemonmovemethodname = Column("pokemonmovemethodname",String(35))
    
class PokemonNickname(Base):
    __tablename__ = 'pokemonnickname'
    pokemonid = Column("pokemonid",Integer,ForeignKey("pokemon.pokemonid"))
    pokemonnickname = Column("pokemonnickname",String(100))
    pokemonnicknameid = Column("pokemonnicknameid",Integer,primary_key=True)
    
class PokemonStat(Base):
    __tablename__ = 'pokemonstat'
    pokemonstatid = Column("pokemonstatid",Integer,primary_key=True)
    pokemonid = Column("pokemonid",Integer,ForeignKey("pokemon.pokemonid"))
    statid = Column("statid",Integer,ForeignKey("stat.statid"))
    pokemonstatvalue = Column("pokemonstatvalue",Integer)
    generationid = Column("generationid",Integer,ForeignKey("generation.generationid"))
    
class PokemonType(Base):
    __tablename__ = 'pokemontype'
    pokemontypeid = Column("pokemontypeid",Integer,primary_key=True)
    pokemonid = Column("pokemonid",Integer,ForeignKey("pokemon.pokemonid"))
    pokemontypeorder = Column("pokemontypeorder",Integer)
    typeid = Column("typeid",Integer,ForeignKey("type.typeid"))
    generationid = Column("generationid",Integer,ForeignKey("generation.generationid"))
    
class Stat(Base):
    __tablename__ = 'stat'
    statid = Column("statid",Integer,primary_key=True)
    statname = Column("statname",String(30))
    statabbreviation = Column("statabbreviation",String(15))
    
class Type(Base):
    __tablename__ = 'type'
    typeid = Column("typeid",Integer,primary_key=True)
    typename = Column("typename",String(20))
    generationid = Column("generationid",Integer,ForeignKey("generation.generationid"))
    
class TypeMatchup(Base):
    __tablename__ = 'typematchup'
    typematchupid = Column("typematchupid",Integer,primary_key=True)
    attackingtypeid = Column("attackingtypeid",Integer,ForeignKey("type.typeid"))
    defendingtypeid = Column("defendingtypeid",Integer,ForeignKey("type.typeid"))
    damagemodifier = Column("damagemodifier",DECIMAL)
    generationid = Column("generationid",Integer,ForeignKey("generation.generationid"))

class Channel(Base):
    __tablename__ = 'channelclean'
    gameid = Column("gameid",Integer,ForeignKey("game.gameid"))
    twitchuserid = Column("twitchuserid",Integer,ForeignKey("twitchuser.twitchuserid"),primary_key=True)

class ChannelCommandRequest(Base):
    __tablename__ = 'channelcommandrequest'
    channelcommandrequestid = Column('channelcommandrequestid',Integer,primary_key=True)
    commandid = Column('commandid',Integer,ForeignKey("command.commandid"))
    channeltwitchuserid = Column('channeltwitchuserid',Integer,ForeignKey('twitchuser.twitchuserid'))
    operanttwitchuserid = Column('operanttwitchuserid',Integer,ForeignKey('twitchuser.twitchuserid'))
    abilityid = Column('abilityid',Integer)
    pokemonid = Column('pokemonid',Integer)
    natureid = Column('natureid',Integer)
    moveid = Column('moveid',Integer)
    gameid = Column('gameid',Integer)
    levelingrateid = Column('levelingrateid',Integer)
    commandselectid = Column('commandselectid',Integer)
    channelcommandrequesttime = Column('channelcommandrequesttime',DateTime)
    channelcommandrequestreturn = Column('channelcommandrequestreturn',String(300))

class ChannelCommandRequestParameter(Base):
    __tablename__ = 'channelcommandrequestparameter'
    channelcommandrequestparameterid = Column('channelcommandrequestparameterid',Integer,primary_key=True)
    channelcommandrequestid = Column("channelcommandrequestid",Integer,ForeignKey('channelcommandrequest.channelcommandrequestid'))
    channelcommandrequestparameter = Column("channelcommandrequestparameter",String(50))

class ChannelDeletion(Base):
    __tablename__ = 'channeldeletion'
    channelid = Column("channelid",Integer,ForeignKey("channel.channelid"),primary_key=True)
    twitchuserid = Column("twitchuserid",Integer,ForeignKey("twitchuser.twitchuserid"))
    deletiontime = Column('deletiontime',DateTime)

class ChannelError(Base):
    __tablename__ = 'channelerror'
    channelerrorid = Column("channelerrorid",Integer,primary_key=True)
    channelcommandrequestid = Column("channelcommandrequestid",Integer,ForeignKey("channelcommandrequest.channelcommandrequestid"))
    errortypeid = Column("errortypeid",Integer,ForeignKey("errortype.errortypeid"))
    channelerrortime = Column("channelerrortime",DateTime)
    channeltwitchuserid = Column("channelid",Integer,ForeignKey("channel.channelid"))

class ChannelOperant(Base):
    __tablename__ = 'channeloperantclean'
    channeltwitchuserid = Column("channeltwitchuserid",Integer,ForeignKey("twitchuser.twitchuserid"),primary_key=True)
    operanttwitchuserid = Column("operanttwitchuserid",Integer,ForeignKey("twitchuser.twitchuserid"),primary_key=True)
    operanttypeid = Column("operanttypeid",Integer,ForeignKey("operanttype.operanttypeid"))

class Command(Base):
    __tablename__ = 'command'
    commandid = Column("commandid",Integer,primary_key=True)
    commandname = Column("commandname",String(35))
    commanddescription = Column("commanddescription",String(300))
    commandtypeid = Column("commandtypeid",Integer,ForeignKey("commandtype.commandtypeid"))
    commandminimumparameters = Column("commandminimumparameters",Integer)
    commandmaximumparameters = Column("commandmaximumparameters",Integer)

class CommandCommandType(Base):
    __tablename__ = 'commandcommandtype'
    commandid = Column("commandid",Integer,primary_key=True)
    commandtypeid = Column("commandtypeid",Integer,ForeignKey("commandtype.commandtypeid"),primary_key=True)

class CommandType(Base):
    __tablename__ = 'commandtype'
    commandtypeid = Column("commandtypeid",Integer,primary_key=True)
    commandtypename = Column("commandtypename",String(50))
    commandtypedescription = Column("commandtypedescription",String(300))

class ErrorType(Base):
    __tablename__ = 'errortype'
    errortypeid = Column("errortypeid",Integer,primary_key=True)
    errortypename = Column("errortypename",String(50))
    errortypedescription = Column("errortypedescription",String(300))

class OperantType(Base):
    __tablename__ = 'operanttype'
    operanttypeid = Column("operanttypeid",Integer,primary_key=True)
    operanttypename = Column("operanttypename",String(50))
    operanttypedescription = Column("operanttypedescription",String(300))

class TwitchUser(Base):
    __tablename__ = 'twitchuser'
    twitchuserid = Column("twitchuserid",Integer,primary_key=True)
    twitchusername = Column("twitchusername",String(100))

############ WAREHOUSE ############

class RandomizerEvolutionCounts(Base):
    __tablename__ = 'randomizerevolutioncountsfull'
    randomizerevolutionid = Column("randomizerevolutionid",Integer,primary_key=True)
    gamegroupid = Column("gamegroupid",Integer,ForeignKey("gamegroup.gamegroupid"))
    basepokemonid = Column("basepokemonid",Integer,ForeignKey("pokemon.pokemonid"))
    targetpokemonid = Column("targetpokemonid",Integer,ForeignKey("pokemon.pokemonid"))
    vanillatargetid = Column("vanillatargetid",Integer,ForeignKey("pokemon.pokemonid"))
    seedcount = Column("seedcount",Integer)

Base.metadata.create_all(engine)

#################################################