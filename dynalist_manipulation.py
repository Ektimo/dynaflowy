import json
# from wrappers.dynalist import DynalistWrapper
import wrappers.dynalist as dyna
from importlib import reload
reload(dyna)

def readConfig(filename="config.json"):
    with open(filename) as json_data_file:
        data = json.load(json_data_file)
    return data

config = readConfig("config.json")

d = dyna.DynalistWrapper(config["dynalistKey"])

d.listFolders()
d.listFiles()
d.listFiles(folder="Ektimo")

d.getFileContent("Test")

d.backupJson("Test", "test.json")
d.backupJson("Test", "test2.json")

d.changelogLive("test.json","Test")
d.changelogLocal("test.json", "test2.json")