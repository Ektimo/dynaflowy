import json
import requests as r
import pandas as pd
# import pdb


class DynalistWrapper(object):
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
        raise NotImplementedError()

    def changelogLocal(self, localFile1, localFile2):
        raise NotImplementedError()
        
    def changelogLive(self, fileName, localFileName):
        raise NotImplementedError()