#!/bin/bash
echo "Current Time: "
date "+%m-%d-%Y %H:%M:%S"
cd /home/stuxnet/dashboard/
git add .
git commit -m "test"
git push
echo "gitPush Done."
