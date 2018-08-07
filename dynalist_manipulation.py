import json
# from wrappers.dynalist import DynalistWrapper
import wrappers.dynalist as dyna
from importlib import reload
reload(dyna)

def readConfig(filename="config.json"):
    with open(filename) as json_data_file:
        data = json.load(json_data_file)
    return data

def getContent(fileContent, nodeId, property='content', maxChar = 100):
    for i in range(len(fileContent)):
        if fileContent[i]['id'] == nodeId:
            try:
                rez = fileContent[i][property]
                if (type(rez).__name__ == 'list'): #in case of list, we return length
                    return len(rez)
                elif (type(rez).__name__ == 'bool'): #in case of bool, we return bool
                    return rez
                else: #in case of string we return maxChar len string
                    if len(rez) > maxChar:
                        return rez[:maxChar]+' ...'
                    else:
                        return rez
            except:
                return None
    raise Exception('Node ')

def parseDiff(dynaWrapper, dictDiff, oldContent, newContent, fileName):
    parsedDiff = []
    for i in range(len(dictDiff)):
        prop = None
        dictDiff_i = dictDiff[i]
        path = dictDiff_i["message"]["path"]
        splitPath = path.split('.')
        #changes in document root - only note parsed
        if len(splitPath) < 2: 
            if splitPath[0] == 'note':
                newValue = dictDiff_i["message"]["new"] #get new value of property
                oldValue = dictDiff_i["message"]["old"] #get old value of property
                content = getContent(newContent, 'root', maxChar=50)
                webLink = dynaWrapper.webURLNode(fileName, None) #change in root of a file
                parsedDiff.append({'type':'CHANGED-notes', 'link': webLink, 'notes':{'old':oldValue,'new':newValue}, 'content':content})
            continue #we continue parsing diffs
        # other changes
        if dictDiff_i['type'] == "ADDED": #added bullet
            content = getContent(newContent, splitPath[-1]) #get content
            numChild =  getContent(newContent, splitPath[-1], property="children") #get num of children
            if len(splitPath)>2:
                webLink = dynaWrapper.webURLNode(fileName, splitPath[-3])
            else:
                webLink = dynaWrapper.webURLNode(fileName, None) #change in root of a file
            parsedDiff.append({'type':'ADDED', 'link': webLink, 'content':content, 'numChild':numChild})
        elif dictDiff_i['type'] == "REMOVED": #removed bullet
            content = getContent(oldContent, splitPath[-1]) #get content
            numChild =  getContent(oldContent, splitPath[-1], property="children") #get num of children
            if len(splitPath)>2:
                webLink = dynaWrapper.webURLNode(fileName, splitPath[-3])
            else:
                webLink = dynaWrapper.webURLNode(fileName, None) #change in root of a file
            parsedDiff.append({'type':'REMOVED', 'link': webLink, 'content':content, 'numChild':numChild})
        else: #type "CHANGED"
            #need to get the property
            prop = splitPath[-1]
            if len(splitPath)>3:
                webLink = dynaWrapper.webURLNode(fileName, splitPath[-4])
            else:
                webLink = dynaWrapper.webURLNode(fileName, None) #change in root of a file
            newValue = dictDiff_i["message"]["new"] #get new value of property
            oldValue = dictDiff_i["message"]["old"] #get old value of property
            if prop == 'content':
                #new text and link to parent
                parsedDiff.append({'type':'CHANGED-content', 'link': webLink, 'content': {'old':oldValue, 'new':newValue}})
            elif prop == 'note':
                #text notes + text bullet + link to parent
                content = getContent(newContent, splitPath[-2], maxChar=50)
                parsedDiff.append({'type':'CHANGED-notes', 'link': webLink, 'notes': {'old':oldValue, 'new':newValue}, 'content':content})
            elif prop == 'checked':
                content = getContent(newContent, splitPath[-2])
                parsedDiff.append({'type':'CHANGED-checked', 'link': webLink, 'content':newValue, 'checked':{'old':oldValue, 'new':newValue}})
            else:
                raise Exception('Propery {} unknown!'.format(prop))
    #return
    return parsedDiff

       
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

parseDiff(d,diffs,old,new,"Test")

