#!/bin/bash
datetimenow=date "+%m-%d-%Y %H:%M:%S"
echo "Current Time: ${datetimenow}"
cd /home/stuxnet/dashboard/
git add .
git commit -m "test"
git push
echo "gitPush Done."
