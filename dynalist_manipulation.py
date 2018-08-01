import json
from wrappers.dynalist import DynalistWrapper

def readConfig(filename="config.json"):
    with open(filename) as json_data_file:
        data = json.load(json_data_file)
    return data

config = readConfig("config.json")

d = DynalistWrapper(config["dynalistKey"])

d.listFolders()
d.listFiles()
d.listFiles(folder="Ektimo")

d.getFileContent("TUS")

#TODO: implement
d.backupJson("","")