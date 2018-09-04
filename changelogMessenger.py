import json
import time
import os
from slacker import Slacker

import wrappers.dynalist as dyna
from helpers import getLocalFileName

import pdb

class ChangelogMessenger:
    __backupBase = ""
    __backupFolder = ""
    __backupFileNames = []
    __channelMapper = []
    __dynalist = None
    __slack = None

    def __init__(self, slackKey, dynalistKey, backupBase, backupFolder, backupFileNames, channelMapper):
        #check fileNames in mapper
        d = [x for x in channelMapper if x["file"] not in backupFileNames]
        if len(d) > 0:
            raise Exception("In mapper are files that do not exists in backupFileNames?!?!")
        self.__backupBase = backupBase
        self.__backupFolder = backupFolder
        self.__backupFileNames = backupFileNames
        self.__channelMapper = channelMapper
        self.__dynalist = dyna.DynalistWrapper(dynalistKey)
        self.__slack = Slacker(slackKey)
        
    def __backupListOfFiles(self, fileList, folder):
        liveList = self.__dynalist.listFiles()
        rezDict = {}
        for f in liveList:
            #if not on list, go to next one
            if f not in fileList:
                continue
            localFileName = getLocalFileName(folder,self.__backupBase+f)
            try:
                self.__dynalist.backupJson(f, localFileName)
                rezDict[f] = localFileName
            except:
                rezDict[f] = "ERROR: backup failed!"
            time.sleep(1) #delay for dynalist getter
        return rezDict
        
    def __getContent(self, fileContent, nodeId, property='content', maxChar = 100):
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
                            return rez[:maxChar]+'...'
                        else:
                            return rez
                except:
                    return None
        raise Exception('Node {} does not exists!'.format(nodeId))

    def __pathToBullets(self, fileName,path,fileContent,numBullets=3):
        #root is the parent
        if (len(path) < 3) | (numBullets < 1):
            return fileName
        pathIDs = [x for x in path if x not in ["children","content","note","checked"]]
        #take max numBullets
        if len(pathIDs) > numBullets:
            pathIDs = pathIDs[-numBullets:]
            contents = [fileName, '...']+[self.__getContent(fileContent,x,maxChar=15) for x in pathIDs]
        else:
            contents = [fileName]+[self.__getContent(fileContent,x,maxChar=15) for x in pathIDs]
        return ' > '.join(contents)
        
    def __slackMessageFormatter(self, fileName, diff):
        if diff['type'] == 'ADDED':
            attach={
                # "pretext": "Path - {}".format(diff['path']),
                "title": "ADDED - {}".format(diff['path']),
                "title_link": diff['link'],
                "text": "- {}\nwith {} children".format(diff['content'],diff['numChild']),
                "color": "good"
            }
        elif diff['type'] == 'REMOVED':
            attach={
                # "pretext": "Path - {}".format(diff['path']),
                "title": "REMOVED - {}".format(diff['path']),
                "title_link": diff['link'],
                "text": "- {}\nwith {} children".format(diff['content'],diff['numChild']),
                "color": "danger"
            }
        elif diff['type'] == 'CHANGED-content':
            attach={
                # "pretext": "Path - {}".format(diff['path']),
                "title": "CHANGED CONTENT - {}".format(diff['path']),
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
                # "pretext": "Path - {}".format(diff['path']),
                "title": "CHANGED NOTES - {}".format(diff['path']),
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
                # "pretext": "Path - {}".format(diff['path']),
                "title": "CHANGED CHECKED - {}".format(diff['path']),
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

    def parseDiff(self, dictDiff, oldContent, newContent, fileName, numBullets=3):
        parsedDiff = []
        for i in range(len(dictDiff)):
            prop = None
            dictDiff_i = dictDiff[i]
            path = dictDiff_i["message"]["path"]
            splitPath = path.split('.')
            # if dictDiff_i["type"] == "ADDED":
            #     pdb.set_trace()
            #changes in document root - only note parsed
            if len(splitPath) < 2: 
                if splitPath[0] == 'note':
                    newValue = dictDiff_i["message"]["new"] #get new value of property
                    oldValue = dictDiff_i["message"]["old"] #get old value of property
                    content = self.__getContent(newContent, 'root', maxChar=50)
                    webLink = self.__dynalist.webURLNode(fileName, None) #change in root of a file
                    parsedDiff.append({'type':'CHANGED-notes', 'link': webLink, 'notes':{'old':oldValue,'new':newValue}, 'content':content, 'path': fileName})
                continue #we continue parsing diffs
            #children are parsed later on
            if (splitPath[-1] == "children"):
                continue
            # other changes
            if dictDiff_i['type'] == "ADDED": #added bullet
                content = self.__getContent(newContent, splitPath[-1]) #get content
                numChild =  self.__getContent(newContent, splitPath[-1], property="children") #get num of children
                if len(splitPath)>2:
                    webLink = self.__dynalist.webURLNode(fileName, splitPath[-3])
                else:
                    webLink = self.__dynalist.webURLNode(fileName, None) #change in root of a file
                parsedDiff.append({'type':'ADDED', 'link': webLink, 'content':content, 'numChild':numChild, 'path': self.__pathToBullets(fileName,splitPath[:-1],newContent,numBullets=numBullets)})
            elif dictDiff_i['type'] == "REMOVED": #removed bullet
                content = self.__getContent(oldContent, splitPath[-1]) #get content
                numChild =  self.__getContent(oldContent, splitPath[-1], property="children") #get num of children
                if len(splitPath)>2:
                    webLink = self.__dynalist.webURLNode(fileName, splitPath[-3])
                else:
                    webLink = self.__dynalist.webURLNode(fileName, None) #change in root of a file
                parsedDiff.append({'type':'REMOVED', 'link': webLink, 'content':content, 'numChild':numChild, 'path':self.__pathToBullets(fileName,splitPath[:-1],oldContent,numBullets=numBullets)})
            else: #type "CHANGED"
                #need to get the property
                prop = splitPath[-1]
                if len(splitPath)>3:
                    webLink = self.__dynalist.webURLNode(fileName, splitPath[-4])
                else:
                    webLink = self.__dynalist.webURLNode(fileName, None) #change in root of a file
                newValue = dictDiff_i["message"]["new"] #get new value of property
                oldValue = dictDiff_i["message"]["old"] #get old value of property
                if prop == 'content':
                    #new text and link to parent
                    parsedDiff.append({'type':'CHANGED-content', 'link': webLink, 'content': {'old':oldValue, 'new':newValue}, 'path': self.__pathToBullets(fileName,splitPath[:-1],newContent,numBullets=numBullets)})
                elif prop == 'note':
                    #text notes + text bullet + link to parent
                    content = self.__getContent(newContent, splitPath[-2], maxChar=50)
                    parsedDiff.append({'type':'CHANGED-notes', 'link': webLink, 'notes': {'old':oldValue, 'new':newValue}, 'content':content, 'path':self.__pathToBullets(fileName,splitPath[:-1],newContent,numBullets=numBullets)})
                elif prop == 'checked':
                    content = self.__getContent(newContent, splitPath[-2])
                    parsedDiff.append({'type':'CHANGED-checked', 'link': webLink, 'content':content, 'checked':{'old':oldValue, 'new':newValue},'path': self.__pathToBullets(fileName,splitPath[:-1],newContent,numBullets=numBullets)})
                else:
                    raise Exception('Propery {} unknown!'.format(prop))
        #return
        return parsedDiff

    def __postToSlack(self, fileName, diffs, channel):    
        attach = []
        for diff in diffs:
            attach.append(self.__slackMessageFormatter(fileName, diff))
            #slack recommends no more than 20 attachments
            if len(attach) > 19:
                self.__slack.chat.post_message(channel=channel,
                    attachments=attach,
                    parse="full",
                    as_user=True
                )
                attach = [] #reset queue
                time.sleep(1) #sleep to not exceed the posting limit in slack
        #there are messages to post
        if len(attach)>0: 
            self.__slack.chat.post_message(channel=channel,
                    attachments=attach,
                    parse="full",
                    as_user=True
                )

    def backupFiles(self):
        return self.__backupListOfFiles(self.__backupFileNames, self.__backupFolder)
    
    def liveChangesToSlack(self, caseSensitive=True):
        self.backupFiles()
        files = []
        for f in os.listdir(self.__backupFolder):
            files.append(self.__backupFolder+'/'+f)
        
        # pdb.set_trace()
        for x in self.__channelMapper:
            fileName = x["file"]
            foi = [f for f in files if fileName in f]
            if len(foi) < 2:
                continue #nothing to compare
            foi.sort()
            old,new,diffs = self.__dynalist.changelogLocal(foi[-2], foi[-1], caseSensitive) #compare last two entries
            rez = self.parseDiff(diffs,old,new,fileName)
            if (len(rez)>0):
                self.__postToSlack(fileName, rez, x["channel"])        
