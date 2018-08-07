import json
# from wrappers.dynalist import DynalistWrapper
import wrappers.dynalist as dyna
from slacker import Slacker

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

def pathToBullets(fileName,path,fileContent,numBullets=3):
    #root is the parent
    if (len(path) <= 3) | (numBullets < 1):
        return fileName
    pathIDs = [x for x in path if x not in ["children","content","note","checked"]]
    #take max numBullets
    if len(pathIDs) > numBullets:
        pathIDs = pathIDs[-numBullets:]
        contents = [fileName, '...']+[getContent(fileContent,x,maxChar=15) for x in pathIDs]
    else:
        contents = [fileName]+[getContent(fileContent,x,maxChar=15) for x in pathIDs]
    return ' > '.join(contents)
       
def parseDiff(dynaWrapper, dictDiff, oldContent, newContent, fileName, numBullets=3):
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
                parsedDiff.append({'type':'CHANGED-notes', 'link': webLink, 'notes':{'old':oldValue,'new':newValue}, 'content':content, 'path': fileName})
            continue #we continue parsing diffs
        # other changes
        if dictDiff_i['type'] == "ADDED": #added bullet
            if (splitPath[-1] == "children"):
                continue #added known later on
            content = getContent(newContent, splitPath[-1]) #get content
            numChild =  getContent(newContent, splitPath[-1], property="children") #get num of children
            if len(splitPath)>2:
                webLink = dynaWrapper.webURLNode(fileName, splitPath[-3])
            else:
                webLink = dynaWrapper.webURLNode(fileName, None) #change in root of a file
            parsedDiff.append({'type':'ADDED', 'link': webLink, 'content':content, 'numChild':numChild, 'path': pathToBullets(fileName,splitPath[:-1],newContent,numBullets=numBullets)})
        elif dictDiff_i['type'] == "REMOVED": #removed bullet
            content = getContent(oldContent, splitPath[-1]) #get content
            numChild =  getContent(oldContent, splitPath[-1], property="children") #get num of children
            if len(splitPath)>2:
                webLink = dynaWrapper.webURLNode(fileName, splitPath[-3])
            else:
                webLink = dynaWrapper.webURLNode(fileName, None) #change in root of a file
            parsedDiff.append({'type':'REMOVED', 'link': webLink, 'content':content, 'numChild':numChild, 'path':pathToBullets(fileName,splitPath[:-1],oldContent,numBullets=numBullets)})
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
                parsedDiff.append({'type':'CHANGED-content', 'link': webLink, 'content': {'old':oldValue, 'new':newValue}, 'path': pathToBullets(fileName,splitPath[:-1],newContent,numBullets=numBullets)})
            elif prop == 'note':
                #text notes + text bullet + link to parent
                content = getContent(newContent, splitPath[-2], maxChar=50)
                parsedDiff.append({'type':'CHANGED-notes', 'link': webLink, 'notes': {'old':oldValue, 'new':newValue}, 'content':content, 'path': pathToBullets(fileName,splitPath[:-1],newContent,numBullets=numBullets)})
            elif prop == 'checked':
                content = getContent(newContent, splitPath[-2])
                parsedDiff.append({'type':'CHANGED-checked', 'link': webLink, 'content':content, 'checked':{'old':oldValue, 'new':newValue},'path': pathToBullets(fileName,splitPath[:-1],newContent,numBullets=numBullets)})
            else:
                raise Exception('Propery {} unknown!'.format(prop))
    #return
    return parsedDiff

def slackMessageFormatter(fileName, diff):
    if diff['type'] == 'ADDED':
        attach={
            "pretext": "Path - {}".format(diff['path']),
            "title": "ADDED",
            "title_link": diff['link'],
            "text": "- {}\nwith {} children".format(diff['content'],diff['numChild']),
            "color": "good"
        }
    elif diff['type'] == 'REMOVED':
        attach={
            "pretext": "Path - {}".format(diff['path']),
            "title": "REMOVED",
            "title_link": diff['link'],
            "text": "- {}\nwith {} children".format(diff['content'],diff['numChild']),
            "color": "danger"
        }
    elif diff['type'] == 'CHANGED-content':
        attach={
            "pretext": "Path - {}".format(diff['path']),
            "title": "CHANGED CONTENT",
            "title_link": diff['link'],
            "fields":[
                {
                    "title": "- {}".format(diff['content']['new']),
                    "value": "- {}".format(diff['content']['old']),
                    "short": False
                }
            ],
            "color": "warning"
        }
    elif diff['type'] == 'CHANGED-notes':
        attach={
            "pretext": "Path - {}".format(diff['path']),
            "title": "CHANGED NOTES",
            "title_link": diff['link'],
            "fields":[
                {
                    "title": "- {}".format(diff['content']),
                    "value": None,
                    "short": True
                },
                {
                    "title": diff['notes']['new'],
                    "value": diff['notes']['old'],
                    "short": False
                }
            ],
            "color": "warning"
        }
    elif diff['type'] == 'CHANGED-checked':
        attach={
            "pretext": "Path - {}".format(diff['path']),
            "title": "CHANGED CHECKED",
            "title_link": diff['link'],
            "fields":[
                {
                    "title": "- {}".format(diff['content']),
                    "value": None,
                    "short": True
                },
                {
                    "title": str(diff['checked']['new']),
                    "value": str(diff['checked']['old']),
                    "short": False
                }
            ],
            "color": "warning"
        }
    else:
        attach={
            "pretext": "ERROR",
            "title": "ERROR",
            "text": json.dumps(diff),
            "color": "danger"
        }
    return attach

def postToSlack(slack, fileName, diffs, channel):    
    attach = []
    for diff in diffs:
        attach.append(slackMessageFormatter(fileName, diff))
        #slack recommends no more than 20 attachments
        if len(attach) > 19:
            slack.chat.post_message(channel=channel,
                attachments=attach,
                parse="full",
                as_user=True
            )
            attach = [] #reset queue
    #there are messages to post
    if len(attach)>0: 
        slack.chat.post_message(channel=channel,
                attachments=attach,
                parse="full",
                as_user=True
            )


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

#########################
###
### slack integration
###
#########################        

# slack = Slacker(config['slackbot'])
# postToSlack(slack, rez, "#testslacker")
