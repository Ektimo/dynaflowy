# Introduction

Python library for possible syncing Workflowy and Dynalist.
Possible problems:
* Dynlist API doesn't track who made change and when


# DynalistWrapper

## Basic usage

'''
d = DynalistWrapper("key")
d.listFolders()
d.listFiles()
d.listFiles("folder2")
d.getFileContent("file123")
'''

## Changelog and backups

### Backups on disk as json files

'''
d.backupJson("fileName", "local.fileName")
'''

### Changelog between files

'''
d.changelogLocal("local.file1","local.file2")
d.changelogLive("fileName","local.fileName")
'''

# Workflowy wrapper

**TODO**