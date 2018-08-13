from changelogMessenger import ChangelogMessenger
from helpers import readConfig

config = readConfig("config.json")

clm = ChangelogMessenger(config["slackbot"], config["dynalistKey"], config["changelogMessenger"]["backupBase"], config["backup"]["location"], config["backup"]["files"], config["changelogMessenger"]["channelMapper"])

clm.liveChangesToSlack()