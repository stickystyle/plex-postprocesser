#!/usr/bin/env bash

# Setup user/group ids
if [ ! -z "${PLEX_UID}" ]; then
  if [ ! "$(id -u plex)" -eq "${PLEX_UID}" ]; then

    # usermod likes to chown the home directory, so create a new one and use that
    # However, if the new UID is 0, we can't set the home dir back because the
    # UID of 0 is already in use (executing this script).
    if [ ! "${PLEX_UID}" -eq 0 ]; then
      mkdir /tmp/temphome
      usermod -d /tmp/temphome plex
    fi

    # Change the UID
    usermod -o -u "${PLEX_UID}" plex

    # Cleanup the temp home dir
    if [ ! "${PLEX_UID}" -eq 0 ]; then
      usermod -d /config plex
      rm -Rf /tmp/temphome
    fi
  fi
fi

if [ ! -z "${PLEX_GID}" ]; then
  if [ ! "$(id -g plex)" -eq "${PLEX_GID}" ]; then
    groupmod -o -g "${PLEX_GID}" plex
  fi
fi