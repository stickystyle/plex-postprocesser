#!/bin/bash

docker run -i -t --rm \
  -e BASE_URL="http://192.168.10.200:32400" \
  -e TOKEN="zU3WTVp2qrm51c2Cz5HM" \
  -e RQ_REDIS_URL="redis://192.168.10.200:6379" \
  -e HB_PRESET="Apple 1080p60 Surround" \
  -v /bucket/plex/transcode:/transcode \
  -v /bucket/media:/data \
  -v /home/rparrish/workingfolder/plex-postprocesser:/opt/plexdvr \
  stickystyle/plex-post $1
