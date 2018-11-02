#!/usr/bin/env bash
date=$(date -d '1 month ago' +%Y-%m)
location=$(jq -r .backup.location config.json)
prefix=$(jq -r .changelogMessenger.backupBase config.json)
#echo "backup-$date.tar.gz $location/$prefix*$date*"
tar -cvzf backup-$date.tar.gz $location/$prefix*$date*

rm -v $location/$prefix*$date*
