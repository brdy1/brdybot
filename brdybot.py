#used to access the config ini file
import configparser
#this is used for accessing the app/api
import requests
#this imports the information schema, sqlalchemy, and more
from schema import *
import json
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
from datetime import datetime
from sqlalchemy.orm import aliased
import re
from app import getCommands, getTwitchID,insert,update,delete,Session

dbschema='pokemon,bot'
config = configparser.ConfigParser()
file = "chatbot.ini"
config.read(file)
host = config['database']['host']
database = config['database']['database']
user = config['database']['user']
password = config['database']['password']
engine = create_engine('postgresql+psycopg2://'+user+':'+password+'@'+host+':5432/'+database,connect_args={'options': '-csearch_path={}'.format(dbschema)})
Base = declarative_base(engine)

Base.metadata.create_all(engine)


def main():
    conn, token, user, readbuffer, server, token = Setup.getConnectionVariables()
    #twitchusers = Setup.getTwitchIDs()
    commanddict = Setup.getCommandDict()
    twitchusers = Setup.getChannels()
    #Setup.updateTwitchNames(twitchusers)
    #twitchusers = Setup.getTwitchIDs()
    for twitchuserid in twitchusers:
        twitchuserid = twitchuserid[0]
        operators = Setup.getOperants(twitchuserid)
        #create a listening thread
        print("create listening thread")
        threading.Thread(target=Bot.ircListen, args=(conn, token, user, twitchuserid, server, operators, commanddict)).start()
        sleep(2.2)

class Bot():
    def ircListen(conn, token, botName, twitchuserid, server, operators, commandDict):
        try:
            listenFlag = True
            channel = Bot.getTwitchUserName(twitchuserid)
            #joining the channel
            server = socket.socket()
            server.connect(conn)
            server.send(bytes('PASS ' + token + '\r\n', 'utf-8'))
            server.send(bytes('NICK ' + botName + '\r\n', 'utf-8'))
            server.send(bytes('JOIN #' + channel + '\r\n', 'utf-8'))
            #listening loop
            print("Starting bot in channel " +channel + " with operants: "+str(operators))
            pattern = re.compile(r'^:[a-zA-Z0-9]{3,25}![a-zA-Z0-9]{3,25}@([a-zA-Z0-9]{3,25})\.tmi\.twitch\.tv\s+PRIVMSG\s+#[a-zA-Z0-9]{3,25}\s+:!(.*?)$', re.M)
            while listenFlag:
                try:
                    message = None
                    response = server.recv(2048).decode('utf-8')
                    if len(response) == 0:
                        continue
                    if "PING" in str(response):
                        server.send(bytes('PONG :tmi.twitch.tv\r\n', 'utf-8'))
                    elif ":!" in str(response):
                        # responsesplit = str(response).split(":!")
                        # if channel == 'brdy':
                        #     print(responsesplit)
                        for requestername, userMessage in map(lambda x: x.groups(), pattern.finditer(response)):
                            try:
                                userMessage = re.sub(' +',' ',userMessage)
                                print(requestername)
                                print(userMessage)
                                command = userMessage.replace("'","''").split(" ")[0].lower().strip()
                                parameters = userMessage.replace("\U000e0000","").replace("\U000e0002","").replace("\U000e001f","").replace("'","''").strip().split(" ")[1:]
                                permissions = (requestername in operators.values()) or (requestername == channel) or (channel == 'brdybot') or (command == "botinfo")
                                if (command in list(commandDict.keys())) and (permissions or requestername == 'brdy'):
                                    print(command)
                                    print(commandDict)
                                    print(twitchuserid)
                                    print(requestername)
                                    print(parameters)
                                    message,ccrid = Bot.doCommand(command,commandDict,twitchuserid,requestername,parameters)
                                    if message:
                                        Bot.chatMessage(message,channel,server)
                                        operators = Setup.getOperants(twitchuserid)
                            except:
                                traceback.print_exc()
                            sleep(1)
                except ConnectionResetError:
                    errortype = "ConnectionResetError"
                    listenFlag = False
                except ConnectionAbortedError:
                    errortype = "ConnectionAbortedError"
                    listenFlag = False
                except ConnectionRefusedError:
                    errortype = "ConnectionRefusedError"
                    listenFlag = False
                except TimeoutError:
                    errortype = "TimeoutError"
                    listenFlag = False
                except IndexError:
                    errortype = "IndexError"
                    listenFlag = False
                except KeyError:
                    errortype = "KeyError"
                    listenFlag = False
                except RuntimeError:
                    errortype = "RuntimeError"
                    listenFlag = False
                except SystemExit:
                    errortype = "SystemExit"
                    listenFlag = False
                except ValueError:
                    errortype = "ValueError"
                    listenFlag = False
                except BrokenPipeError:
                    errortype = "BrokenPipeError"
                    listenFlag = False
                except FileNotFoundError:
                    errortype = "FileNotFoundError"
                    listenFlag = False
                except Exception:
                    errortype = "OtherError"
                    listenFlag = False
        finally:
            if not listenFlag:
                Bot.logException(errortype,twitchuserid)

    def chatMessage(messageString, channel, server):
        x = 1
        if len(messageString) > 299:
            if ' // ' in messageString:
                messagelist = messageString.split('//')
                for message in messagelist:
                    server.send(bytes('PRIVMSG #'+ channel + ' :'+message.replace("//","")+' \r\n', 'utf-8'))
            
            else:
                messagecount = len(messageString)/299
                for x in range(0,math.ceil(messagecount)):
                    splitmsg = messageString[x*299:(x+1)*299]
                    server.send(bytes('PRIVMSG #'+ channel + ' :'+splitmsg.replace("//","")+' \r\n', 'utf-8'))
        else:
            server.send(bytes('PRIVMSG #'+ channel + ' :'+messageString.replace("//","")+' \r\n', 'utf-8'))  

    def logException(errortype,twitchuserid):
        session = Session(engine)
        now = datetime.now()
        channel = Bot.getTwitchUserName(twitchuserid)
        try:
            with open('errorlog.txt', 'a') as f:
                f.write(str(now)+' | '+errortype+' | '+str(twitchuserid)+' | '+str(channel)+'\r\n')
        finally:
            session.close()
        conn, token, user, readbuffer, server, token = Setup.getConnectionVariables()
        operators = Setup.getOperants(twitchuserid)
        commanddict = Setup.getCommandDict()
        threading.Thread(target=Bot.ircListen, args=(conn, token, user, twitchuserid, server, operators, commanddict)).start()

    def logCommand(commandid,twitchuserid,requestername,message,parameters=None,commandtype=None,returnid=None):
        session = Session(engine)
        operanttwitchuserid = getTwitchID(requestername)
        if commandtype != 'game':
            gameid = session.query(Channel.gameid).filter(Channel.twitchuserid==twitchuserid).first()[0]
        try:
            values = {'commandid':commandid,'channeltwitchuserid':twitchuserid,'operanttwitchuserid':operanttwitchuserid,'channelcommandrequestreturn':message}
            if commandtype != 'game':
                values['gameid'] = gameid
            if returnid:
               values[commandtype+'id'] = returnid
            stmt = insert(ChannelCommandRequest).values(values)
            ccrid = session.execute(stmt).inserted_primary_key[0]
            session.commit()
        except:
            session.rollback()
            traceback.print_exc()
        finally:
            session.close()
        if parameters:
            values = []
            for parameter in parameters:
                values.append({'channelcommandrequestid':ccrid,'channelcommandrequestparameter':parameter})
            try:
                stmt = insert(ChannelCommandRequestParameter).values(values)
                session.execute(stmt)
                session.commit()
            except:
                session.rollback()
                traceback.print_exc()
            finally:
                session.close()
        return ccrid

    def doCommand(command,commandDict,twitchuserid,requestername,parameters=None):
        minparam = commandDict[command]['minimum']
        maxparam = commandDict[command]['maximum']
        commandtype = commandDict[command]['type']
        commandid = commandDict[command]['commandid']
        if minparam > 0:
            try:
                parametercount = len(parameters)
            except:
                traceback.print_exc()
                parametercount = 0
            finally:
                if parametercount > (maxparam if maxparam is not None else 999) or parametercount < minparam:
                    # helpmsg = requests.get("http://127.0.0.1:5000/api/v2.0//api/v2.0/help/"+command,params=params)
                    message = "The "+command+" command requires "
                    if minparam is not None:
                        message += "at least "+str(minparam).lower()
                        if maxparam is not None:
                            message += " and "
                    if maxparam is not None:
                        message += "at max"+str(maxparam).lower()
                    if minparam is None and maxparam is None:
                        message += "no"
                    message += " parameters. Use '!help "+command+" for more help."
                    return message
        params = {  'twitchuserid':twitchuserid,
                    'requestername':requestername
                    }
        url = "http://127.0.0.1:5000/api/v2.0/"+command+"/"
        if parameters:
            url += ' '.join(parameters)
        print(twitchuserid)
        print(requestername)
        if command == 'join' and twitchuserid == 687207983:
            message = Bot.addClient(requestername)
            returnid = None
        elif command == 'brdybotleave' and twitchuserid == getTwitchID(requestername):
            message,returnid = Bot.removeChannel(twitchuserid)
        else:
            try:
                response = requests.get(url,params=params)
                message = json.loads(response.text)['message']
                returnid = json.loads(response.text)['returnid']
                print(message)
            except:
                message = "There was an error executing the "+command+" command with the given parameters. Check your parameters and try again. Use '!help "+command+"' for more help."
                ccrid = None
                returnid = None
                traceback.print_exc()
        ccrid = Bot.logCommand(commandid,twitchuserid,requestername,message,parameters,commandtype,returnid)
        return message,ccrid

    def getTwitchUserName(twitchuserid):
        session = Session(engine)
        try:
            twitchusername = session.query(TwitchUser.twitchusername).filter(TwitchUser.twitchuserid == twitchuserid).first()
        except:
            session.rollback()
            traceback.print_exc()
        finally:
            session.close()
        print(twitchusername)
        return twitchusername[0]

    def addClient(requestername):
        session = Session(engine)
        ## Default successflag to false
        successflag = False
        ## fetch twitch userid from twitch api based on requester name
        twitchuserid = getTwitchID(requestername)
        #########
        ## try to insert a new record to the TwitchUser table
        ## ###
        ## if there's an error, this means that either their name has changed or they're already an operant in another channel
        ## therefore, update the TwitchUser record using the requestername
        try:
            inserttwitchid = insert(TwitchUser).values(twitchuserid=twitchuserid,twitchusername=requestername).on_conflict_do_nothing(index_elements=['twitchuserid'])
            insertedtwitchuserid = session.execute(inserttwitchid).inserted_primary_key[0]
            session.commit()
        except:
            print("error inserting twitchuser")
            session.rollback()
            traceback.print_exc()
        finally:
            session.close()
        ## try to add the twitchuserid to the Channel table
        try:
            try:
                insertchannelid = insert(Channel).values(twitchuserid=twitchuserid,gameid=10).on_conflict_do_nothing(index_elements=['twitchuserid'])
                channelid = session.execute(insertchannelid).inserted_primary_key[0]
                session.commit()
                successflag = True
            except:
                print("error inserting channel")
                session.rollback()
                traceback.print_exc()
            try:
                insertoperant = insert(ChannelOperant).values(channeltwitchuserid=twitchuserid,operanttwitchuserid=twitchuserid,operanttypeid=1)
                channeloperantid = session.execute(insertoperant).inserted_primary_key[0]
                session.commit()
                # set the successflag to true
                successflag = True
            except:
                print("error inserting operant")
                session.rollback()
                traceback.print_exc()
            finally:
                session.close()
        finally:
            try:
                stmt = delete(ChannelDeletion).where(ChannelDeletion.twitchuserid == twitchuserid)
                session.execute(stmt)
                session.commit()
                # set the successflag to true
                successflag = True
            except:
                print("error deleting channeldeletion record")
                session.rollback()
                traceback.print_exc()
            finally:
                session.close()
        ## close the session
        session.close()
        ## By this point, the user should have a record in the TwitchUser table and the Channel table and NO record in the ChannelDeletion table.
        ## Let's create a new thread as long as there was a success event
        if successflag:
            conn, token, user, readbuffer, server, token = Setup.getConnectionVariables()
            commanddict = Setup.getCommandDict()
            operantDict = Setup.getOperants(twitchuserid)
            threading.Thread(target=Bot.ircListen, args=(conn, token, user, twitchuserid, server, operantDict, commanddict)).start()
            message = '@'+requestername+""" - Successfully added you to the userlist. Game was set to FireRed. Note that I store usage data but I only report on it anonymized or in aggregate."""
        else:
            message = '@'+requestername+""" - Something went wrong or I am in your channel already. If I'm still not talking there, be sure no words I use (like PP) are banned, and that your channel is not set to followers only."""
        return message

    def removeChannel(twitchuserid):
        session = Session(engine)
        try:
            stmt = (insert(ChannelDeletion).values(twitchuserid=twitchuserid))
            session.execute(stmt)
        except:
            session.rollback()
            traceback.print_exc()
        finally:
            session.close()
        return {'message':'Successfully removed you from the channel list.','returnid':None}

class Setup():
    def getCommandDict():
        session = Session(engine)
        commands = session.query(Command.commandid,Command.commandname,CommandType.commandtypename,Command.commandminimumparameters,Command.commandmaximumparameters).\
            join(CommandType,Command.commandtypeid == CommandType.commandtypeid,isouter=True).order_by(Command.commandname).all()
        commanddict = {}
        for command in commands:
            commandid,commandname,commandtype,commandmin,commandmax = command
            commanddict[commandname] = {'commandid':commandid,
                                    'type':commandtype,
                                    'minimum':commandmin,
                                    'maximum':commandmax}
        print(commanddict)
        return commanddict

    def getOperants(twitchuserid):
        print("getting operants")
        session = Session(engine)
        ChannelTwitch = aliased(TwitchUser)
        OperantTwitch = aliased(TwitchUser)
        print(twitchuserid)
        try:
            channelusers = session.query(ChannelTwitch.twitchusername,OperantTwitch.twitchusername,OperantTwitch.twitchuserid).\
                            select_from(ChannelOperant).\
                            join(ChannelTwitch,ChannelOperant.channeltwitchuserid == ChannelTwitch.twitchuserid).\
                            join(OperantTwitch,ChannelOperant.operanttwitchuserid == OperantTwitch.twitchuserid).\
                            filter(ChannelTwitch.twitchuserid == twitchuserid).distinct().all()
        except:
            session.rollback()
            traceback.print_exc()
        finally:
            session.close()
        print(channelusers)
        twitchusername = Bot.getTwitchUserName(twitchuserid)
        operantdict = {twitchuserid:twitchusername}
        for channelname,username,userid in channelusers:
            operantdict[userid] = username
        print(operantdict)
        return operantdict

    def getChannels():
        session = Session(engine)
        try:
            deletedchannels = session.query(ChannelDeletion.twitchuserid)
            twitchusers = session.query(Channel.twitchuserid).order_by(Channel.twitchuserid).all()
        except:
            session.rollback()
            traceback.print_exc()
        finally:
            session.close()
        print(twitchusers)
        return twitchusers

    def getTwitchIDs():
        session = Session(engine)
        try:
            twitchids = session.query(TwitchUser.twitchuserid).all()
        except:
            traceback.print_exc()
        finally:
            session.close()
        Setup.updateTwitchNames(twitchids)
        return twitchids

    def updateTwitchNames(twitchids):
        session = Session(engine)
        print("Updating twitch ids...")
        secret = config['idfetch']['secret']
        clientid = config['idfetch']['clientid']
        AutParams = {'client_id': clientid,
                'client_secret': secret,
                'grant_type': 'client_credentials'
                }
        authURL = 'https://id.twitch.tv/oauth2/token'
        AutCall = requests.post(url=authURL, params=AutParams) 
        access_token = AutCall.json()['access_token']
        for twitchid in twitchids:
            try:
                url = 'https://api.twitch.tv/helix/users?id='+str(twitchid[0])
                headers = {
                    'Authorization':"Bearer " + access_token,
                    'Client-Id':clientid
                }
                response = requests.get(url,headers=headers)
                twitchusername = response.json()['data'][0]['login']
                print("Updating "+str(twitchid)+" to "+twitchusername)
                stmt = (update(TwitchUser).where(TwitchUser.twitchuserid == twitchid[0]).values(twitchusername=twitchusername))
                session.execute(stmt)
            except:
                traceback.print_exc()
                session.rollback()
        session.commit()
        session.close()

    def getConnectionVariables():
        #parameters for twitch irc server
        connection_data = ('irc.chat.twitch.tv', 6667)
        config = configparser.ConfigParser()
        file = "chatbot.ini"
        config.read(file)
        token = config['chatbot']['token']
        botName = "brdybot"
        readbuffer = ''
        server = socket.socket()
        return connection_data, token, botName, readbuffer, server, token

if __name__ == "__main__":
    main()