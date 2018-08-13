import json
import os

import wrappers.dynalist as dyna
from helpers import *
import changelogMessenger as clm

# from importlib import reload
# reload(dyna)
# reload(clm)


config = readConfig("config.json")

d = dyna.DynalistWrapper(config["dynalistKey"])

d.listFolders()
d.listFiles()
d.listFiles(folder="Ektimo")

d.getFileContent("Test")

d.backupJson("Test", "test.json")
d.backupJson("Test", "test2.json")

old,new,diffs = d.changelogLive("test.json","Test")
old,new,diffs = d.changelogLive("test2.json","Test")
old,new,diffs = d.changelogLocal("test.json", "test2.json")

rez = parseDiff(d,diffs,old,new,"Test")

backupListOfFiles(d,config["backup"]["files"],config["backup"]["location"])

#########################
###
### slack integration
###
#########################        

# slack = Slacker(config['slackbot'])
# postToSlack(slack, "Test", rez, "#testslacker")


##################
###
### Test multiple files, multiple changes
###
##################

slack = Slacker(config['slackbot'])

files = []
for f in os.listdir("backup"):
    files.append("backup/"+f)

fileName = config["backup"]["files"][1]
foi = [f for f in files if fileName in f]
foi.sort()
for i in range(1,len(foi)):
    old,new,diffs = d.changelogLocal(foi[i-1], foi[i])
    rez = parseDiff(d,diffs,old,new,fileName)
    if (len(rez)>0):
        postToSlack(slack, fileName, rez, "#testslacker")