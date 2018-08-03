import json
import requests as r
import pandas as pd
import jsoncompare.jsoncompare as comparer
import pdb


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

    def __url_node(self, fileId, nodeId):
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
                rez['content'] = current['content']
                rez['note'] = current['note']
                rez['checked'] = current['checked']
                rez['parent'] = 'root'
                rez['children'] = self.__toDictRecursion(jsonContent, 'root', current['children'])
                return rez

        raise Exception("Root not found in jsonContent!")

    def __toDictRecursion(self, jsonContent, parent, children):
        rez = dict()

        k = 0
        while k < len(jsonContent):
            current = jsonContent[k]
            if (current['id'] not in children):
                k += 1
                continue
            del jsonContent[k]
            newDict = dict()
            newDict['content'] = current['content']
            newDict['note'] = current['note']
            newDict['checked'] = current['checked']
            newDict['parent'] = parent
            if 'children' in current:
                newDict['children'] = self.__toDictRecursion(jsonContent, current['id'], current['children'])
                rez[current["id"]] = newDict
            else: #end recursion
                rez[current["id"]] = newDict

        return rez


    def getFileContent(self, fileName):
        file_id = self.__files.loc[self.__files.title==fileName]
        file_id = file_id.iloc[0]["id"]
        # pdb.set_trace()
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
        data = self.getFileContent(fileName)
        data = json.dumps(data, indent=4)
        with open(localFileName, 'w') as outfile:
            outfile.writelines(data)
        return True

    def changelogLocal(self, localFileOld, localFileNew):
        data1 = open(localFileOld, 'r').read()
        data2 = open(localFileNew, 'r').read()
        data1 = json.loads(data1)
        data2 = json.loads(data2)
        
        dataOld = self.__toDict(data1)
        dataNew = self.__toDict(data2)
        diffs = comparer.compare(dataOld, dataNew)
        return diffs
        
    def changelogLive(self, localFileNameOld, fileNameLiveNew):
        # pdb.set_trace()
        data = self.getFileContent(fileNameLiveNew)
        data2 = open(localFileNameOld, 'r').read()
        dataLive = self.__toDict(data)
        dataFile = self.__toDict(json.loads(data2))
        diffs = comparer.compare(dataFile,dataLive)
        return diffs