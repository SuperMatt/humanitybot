#! /usr/bin/env python
import socket
import sys
import re
import threading
from datetime import datetime
from datetime import timedelta
import select
import functions

class IRCConnector( threading.Thread):
    def __init__ (self, host, port):
        self.host = host
        self.port = port
        self.channel = "#cah"
        self.identity = "superbot"
        self.realname = "superbot"
        self.hostname = "supermatt.net"
        self.botname = "humanitybot"
        self.allmessages = []
        self.lastmessage = datetime.now()
        self.pulsetime = 500
        threading.Thread.__init__ ( self )

    def output(self, message):
        print("Server: %s\nMessage:%s\n" %(self.host, message))

    def say(self, message):
        #print "sending %s" % message
        messagetosend = "PRIVMSG %s :%s\n" %(message["channel"], message["message"])
        self.s.send(messagetosend)

    def run (self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            print 'Failed to create socket'
            sys.exit()

        remote_ip = socket.gethostbyname(self.host)
        self.output(remote_ip)

        self.s.connect((remote_ip, self.port))
        self.s.setblocking(0)
        message1 = "NICK %s\r\n" %self.botname
        message2 = 'USER %s %s %s :%s\r\n' %(self.identity, self.hostname, self.host, self.realname)
        self.s.send(message1)
        self.s.send(message2)

        g = functions.Game(self)


        while 1:
            line = None
            message = None

            ready = select.select([self.s], [], [], 0.1)
            if ready[0]:
                line = self.s.recv(250)

            if line:

                #self.output(line)
                line.strip()
                splitline = line.split(" :")

                if  "PING" in splitline[0]:
                    pong = "PONG %s" %splitline[1]
                    self.output(pong)
                    self.s.send(pong)

                if re.search(":End of /MOTD command.", line):
                        joinchannel = "JOIN %s\n" %self.channel
                        self.output(joinchannel)
                        self.s.send("PRIVMSG nickserv :identify hum4n1ty\n")
                        self.s.send(joinchannel)
                        self.inchannel = True

                if re.search("PRIVMSG", line):
                    details = line.split()
                    user = details[0].split("!")
                    username = user[0][1:]
                    channel = details[2]
                    messagelist = details[3:]
                    message = " ".join(messagelist)[1:]
                    lower = message.lower()

                    if channel == self.botname:
                        channel = username

                    if lower == "$kill":
                        self.s.send("QUIT :Bot quit\n")
                    elif lower == "$test":
                        self.allmessages.append({"message": "test message", "channel": channel})
                    elif lower == "$reload":
                        try:
                            reload(functions)
                            self.allmessages.append({"message": "Reloaded functions", "channel": channel})
                        except:
                            self.allmessages.append({"message": "Unable to reload due to errors", "channel": channel})
                    else:
                        self.allmessages += functions.actioner(g, message, username, channel, self.channel)

                if re.search(":Closing Link:", line):
                    sys.exit()

            if g.inprogress or g.starttime:
                self.allmessages += functions.gameLogic(g, message, username, channel, self.channel)
            line = None
            message = None
            timestamp = datetime.now()
            if len(self.allmessages) > 0:
                newtime = self.lastmessage + timedelta(milliseconds = self.pulsetime)
                if timestamp > newtime:
                    #print self.allmessages
                    currmess = self.allmessages.pop(0)
                    self.say(currmess)
                    self.lastmessage = timestamp
            #print self.allmessages


irc_connections = [{
                        "host": "irc.darkmyst.org",
                        "port": 6667,
                        "channels": ["#cah"]
                    }]

for irc in irc_connections:
    IRCThread = IRCConnector(irc['host'], irc['port'])
    IRCThread.start()
