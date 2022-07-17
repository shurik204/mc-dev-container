#!/bin/sh

#####################
# For testing only! #
#####################

umount /development/servers/dev-server1
umount /development/servers/dev-server2
umount /development/servers/dev-server3
docker stop development
docker rm development
rm -r /development