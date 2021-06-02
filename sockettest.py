import socket

connection_data = ('irc.chat.twitch.tv', 6667)
token = 'oauth:b0dmrp1p5k6n2agsmz224lp47unrvj'
user = 'brdybot'
channel = '#Yardomaster'
readbuffer = ''

server = socket.socket()
server.connect(connection_data)
server.send(bytes('PASS ' + token + '\r\n', 'utf-8'))
server.send(bytes('NICK ' + user + '\r\n', 'utf-8'))
server.send(bytes('JOIN ' + channel + '\r\n', 'utf-8'))

server.send(bytes('PRIVMSG '+ channel + ' :testing\r\n', 'utf-8'))

while True:
    print(server.recv(2048))