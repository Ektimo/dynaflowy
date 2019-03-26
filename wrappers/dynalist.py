import json
import requests as r
import pandas as pd
import jsoncompare.jsoncompare as comparer
import pdb
import re


class DynalistWrapper(object):
    __webUrl = "https://dynalist.io/d/"
    __url_base = "https://dynalist.io/api/v1/"
    __permission = {
        0: "No access",
        1: "Read only",
        2: "Edit rights",
        3: "Manage",
        4: "Owner"
    }

    @staticmethod
    def __exception(resp):
        return "{}: {}".format(resp["_code"], resp["_msg"])

    def __url(self, path):
        return self.__url_base + path

    def webURLNode(self, fileName, nodeId=None):
        fileId = self.__files.loc[self.__files.title==fileName]
        fileId = fileId.iloc[0]["id"]
        if nodeId is None:
            return self.__webUrl + fileId
        else:
            return self.__webUrl + fileId + "#z=" + nodeId

    def __init__(self, api_key):
        self.__api_key = api_key
        self.__files = self.__getFileList()

    def __json_data(self, fileId=None):
        rez = {
            "token": self.__api_key
        }
        if fileId != None:
            rez["file_id"] = fileId
        return rez
    
    def __getFileList(self):
        files_json = r.post(self.__url("file/list"), json=self.__json_data()).json()
        if (files_json["_code"] != "Ok"):
           raise Exception(self.__exception(files_json)) 

        rez = pd.DataFrame.from_dict(files_json["files"])
        rez["perm_text"] = [self.__permission[rez["permission"][i]] for i in range(len(rez["permission"]))]
        return rez

    def __toDict(self, jsonContent):
        rez = dict()
        
        for i in range(len(jsonContent)):
            current = jsonContent[i]
            if (current['id'] == 'root'):
                jsonContent.remove(current)
                try:
                    rez['content'] = current['content']
                except:
                    rez['content'] = ''
                try:
                    rez['note'] = current['note']
                except:
                    rez['note'] = ''
                try:
                    rez['checked'] = current['checked']
                except:
                    rez['checked'] = False
                rez['parent'] = 'root'
                rez['children'] = self.__toDictRecursion(jsonContent, 'root', current['children'])
                return rez

        raise Exception("Root not found in jsonContent!")

    def __toDictRecursion(self, jsonContent, parent, children):
        rez = dict()

        k = 0
        maxPass = 2
        currentPass = 0
        while (len(jsonContent) > 0) and (currentPass < maxPass): #we must empty the initial data
            k = k % len(jsonContent) #what if deleted the last one
            current = jsonContent[k]
            if (current['id'] not in children):
                k = (k+1)%len(jsonContent) # to recycle trough data
                if (k == 0):
                    currentPass += 1
                continue
            del jsonContent[k]
            newDict = dict()
            try:
                newDict['content'] = current['content']
            except:
                newDict['content'] = ''
            try:
                newDict['note'] = current['note']
            except:
                newDict['note'] = ''
            try:
                newDict['checked'] = current['checked']
            except:
                newDict['checked'] = False
            newDict['parent'] = parent
            if 'children' in current:
                newDict['children'] = self.__toDictRecursion(jsonContent, current['id'], current['children'])
                rez[current["id"]] = newDict
            else: #end recursion
                rez[current["id"]] = newDict

        return rez

    def __findPath(self, contentDict, path='', nodeId=''):
        if 'children' in contentDict:
            if nodeId in contentDict['children']:
                return path
            else:
                #get in for all children and wait if one returns
                for child in contentDict['children']:
                    found = self.__findPath(contentDict=contentDict['children'][child], path=path+"."+child, nodeId=nodeId)
                    if (found != None):
                        return found
        else:
            return None #not found in that branch

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

    def __parsePath(self, path, fileContent,numBullets=3):
        #root is the parent
        pathSplit = path.split(".")
        fileName = pathSplit[0]
        if (len(path) < 3) | (numBullets < 1):
            return fileName
        path = pathSplit[1:]
        pathIDs = [x for x in path if x not in ["children","content","note","checked"]]
        #take max numBullets
        if len(pathIDs) > numBullets:
            pathIDs = pathIDs[-numBullets:]
            contents = [fileName, '...']+[self.__getContent(fileContent,x,maxChar=15) for x in pathIDs]
        else:
            contents = [fileName]+[self.__getContent(fileContent,x,maxChar=15) for x in pathIDs]
        return ' > '.join(contents)

    def getFileContent(self, fileName):
        try:
            file_id = self.__files.loc[self.__files.title==fileName]
            file_id = file_id.iloc[0]["id"]
        except:
            raise Exception('File {} not found! Check your fileName!'.format(fileName))
        
        content = r.post(
            self.__url("doc/read"),
            json=self.__json_data(fileId=file_id)
        ).json()
        if content["_code"] != "Ok":
            raise Exception(self.__exception(content))

        return content["nodes"]

    def listFiles(self, folder=None):
        if folder != None:
            folder = self.__files.loc[(self.__files.title==folder) & (self.__files.type=="folder")]
            # pdb.set_trace()
            rez = self.__files.loc[self.__files.id.isin(folder.iloc[0]["children"])]["title"]
        else:
            rez = self.__files.loc[self.__files.type=="document"]["title"]
        return rez.tolist()
    
    def listFolders(self):
        return self.__files.loc[self.__files.type=="folder"]["title"].tolist()
        
    def backupJson(self, fileName, localFileName):
        try:
            data = self.getFileContent(fileName)
            dataRet = data
            data = json.dumps(data, indent=4)
            with open(localFileName, 'w') as outfile:
                outfile.writelines(data)
            
            #returns content of a file
        except Exception as e:
            raise e
        return dataRet

    def changelogLocal(self, localFileOld, localFileNew, caseSensitive=True):
        data1 = open(localFileOld, 'r').read()
        data2 = open(localFileNew, 'r').read()
        data1 = json.loads(data1)
        data2 = json.loads(data2)
        dataO = data1.copy()
        dataN = data2.copy()
        
        dataOld = self.__toDict(data1)
        dataNew = self.__toDict(data2)
        diffs = comparer.compare(dataOld, dataNew, caseSensitive)
        return [dataO, dataN, diffs] #return old,new,diffs
        
    def changelogLive(self, localFileNameOld, fileNameLiveNew, caseSensitive=True):
        data = self.getFileContent(fileNameLiveNew)
        dataN = data.copy()
        data2 = open(localFileNameOld, 'r').read()
        dataFile = json.loads(data2)
        dataO = dataFile.copy()
        dataLive = self.__toDict(data)
        dataFile = self.__toDict(dataFile)
        diffs = comparer.compare(dataFile, dataLive, caseSensitive)
        return [dataO, dataN, diffs] #return old,new,diffs

    def filterTags(self, fileName, userTags=None, actionTags=None, checkNotes=False):
        content = self.getFileContent(fileName)
        content2 = content.copy()
        dataDict = self.__toDict(content2)
        #filter nodes with tags
        if userTags != None:
            filteredNodes = [node for node in content if (re.search("|".join(userTags),node["content"])!=None) | (checkNotes & (re.search("|".join(userTags),node["note"])!=None))]
            if actionTags != None:
                filteredNodes = [node for node in filteredNodes if (re.search("|".join(actionTags),node["content"])!=None) | (checkNotes & (re.search("|".join(actionTags),node["note"])!=None))]
        elif actionTags != None:
                filteredNodes = [node for node in content if (re.search("|".join(actionTags),node["content"])!=None) | (checkNotes & (re.search("|".join(actionTags),node["note"])!=None))]
        else:
            raise Exception("At least one of the userTags or actionTags should be list!")
        filtered = []
        for n in filteredNodes:
            #get path of node in dict and save relevant data
            # pdb.set_trace()
            path = self.__findPath(contentDict=dataDict, path=fileName, nodeId=n['id'])
            path_name = self.__parsePath(path, content)
            filtered.append({'path': path_name, 'content': n['content'], 'note':n['note']})
                
        return filtered
        
