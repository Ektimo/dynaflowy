import json
import time
import os.path as p

def readConfig(filename="config.json"):
    with open(filename) as json_data_file:
        data = json.load(json_data_file)
    return data

def getLocalFileName(folder, f):
    t = time.strftime("%Y-%m-%d %H-%M",time.localtime())
    fullName = "{}/{}_{}.json".format(folder, f, t)
    i = 0
    exists = p.isfile(fullName)
    while  exists:
        i += 1
        fullName = "{}/{}_{}_{}.json".format(folder, f, t,i)
        exists = p.isfile(fullName)
    return fullName
