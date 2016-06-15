#!/bin/bash
# This is to be parked in /gpfs/runtime/bin, owned by root.

export PATH=/bin:/usr/bin

# The kill is done twice to avoid funny timing issues.
for i in `ps aux | egrep -v -e "^root|^rpc|^dbus|^ntp|^munge|^68|unclutter|^USER" | awk '{print $2}' ` ; do 
	kill $i  
done 

sleep 2

for i in `ps aux | egrep -v -e "^root|^rpc|^dbus|^ntp|^munge|^68|unclutter|^USER" | awk '{print $2}' ` ; do 
	kill -KILL $i  
done 
