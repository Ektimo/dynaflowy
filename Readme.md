# Introduction

Python library for getting Dynalist files and changes.
Possible use cases:
* Backup Dynalist lists
* Post changes between syncs to slack
* Filter tags for automatic reminders, since filtering is pretty awsome in Dynalist


# DynalistWrapper

## Basic usage

```
d = DynalistWrapper("key")
d.listFolders()
d.listFiles()
d.listFiles("folder2")
d.getFileContent("file123")
```

## Changelog and backups

### Backups on disk as json files

```
d.backupJson("fileName.Live", "local.fileName")
```

### Changelog between files

```
d.changelogLocal("local.file.old","local.file.new")
d.changelogLive("local.file.old","fileName.Live")
```

# Automatic integration of changes to Slack

With ChangelogMessenger it is possible to just run crontabJob and get the changelog with previous version to Slack. All you need to do is (assuming you have in the config file changelogMessenger set):

```
clm.liveChangesToSlack()
```
