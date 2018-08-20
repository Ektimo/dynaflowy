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

#########################
###
### slack integration
###
#########################        

dts = clm.ChangelogMessenger(config["slackbot"], config["dynalistKey"], config["changelogMessenger"]["backupBase"], config["backup"]["location"], config["backup"]["files"], config["changelogMessenger"]["channelMapper"])

fileBase = config["backup"]["location"]+"/"+config["changelogMessenger"]["backupBase"]+config["backup"]["files"][2]
old,new,diffs = d.changelogLocal(fileBase+"_2018-08-20 09-00.json", fileBase+"_2018-08-20 12-00.json")

rez = dts.parseDiff(diffs,old,new,config["backup"]["files"][2])
