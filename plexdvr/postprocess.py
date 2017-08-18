#!/usr/bin/env python
import re
import datetime
import subprocess
import tempfile
import os
import shutil
import logging

from plexapi.server import PlexServer

BASE_URL = os.environ.get('BASE_URL')
TOKEN = os.environ.get('TOKEN')

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


class PlexPostProcess(object):
    def __init__(self, baseurl, token):
        logger.info("Init PlexServer @ %s", baseurl)
        self.plex = PlexServer(baseurl, token)

    @staticmethod
    def parse_filename(file_name):
        res = dict(item=None, season=None, episode=None, item_type=None, year=None, title=None)
        title_episode = re.search(
            "\.grab/\w+/(?P<item>.*)\((?P<year>\d+)\)(\s-\s(?P<episode>.*)\s-\s(?P<title>.*))?\.\w+", file_name)
        if title_episode:
            logger.debug("%s is Show", file_name)
            groups = title_episode.groupdict()
            res['item'] = groups['item'].strip()
            res['year'] = int(groups['year'])
            if groups['episode']:
                # Show
                res['item_type'] = 'Show'
                res['title'] = groups['title'].strip()
                episode = groups['episode'].strip()

                reg_episode = re.search("S(\d+)E(\d+)", episode)
                if reg_episode:
                    res['season'] = int(reg_episode.groups()[0].strip())
                    res['episode'] = int(reg_episode.groups()[1].strip())
                    return res
                else:
                    date_episode = datetime.datetime.strptime(episode.strip(), "%Y-%m-%d %H %M %S")
                    res['season'] = date_episode.year
            else:
                logger.debug("%s is Movie", file_name)
                # Movie
                res['item_type'] = 'Movie'
        return res

    @staticmethod
    def get_item_path(item):
        for part in item.iterParts():
            if "Plex Versions" in part.file:
                logger.debug("%s is a plex version", part.file)
                continue
            if os.path.isfile(part.file):
                logger.info("The file for %s is %s", item, part.file)
                return part.file

    def get_episode(self, title, search_file):
        logger.info("Searching for %s with filename %s", title, search_file)
        search_res = self.plex.library.search(title=title)
        logger.info("Found matching items %s", search_res)
        if not search_res:
            logger.error("Did not find an item for %s with filename %s", title, search_file)
        for show in search_res:
            try:
                for episode in show.episodes():
                    logging.debug("Checking episode %s", episode)
                    for part in episode.iterParts():
                        file_name = part.file.split('/')[-1]
                        if file_name == search_file:
                            return episode
            except TypeError:
                logger.debug("Item looks to be a movie")
                # Movie
                for part in show.iterParts():
                    file_name = part.file.split('/')[-1]
                    if file_name == search_file:
                        return show

    def get_active_sessions(self):
        return self.plex.sessions()


def comskip(file_path):
    print("comskip", file_path)
    subprocess.check_call(['python', '/opt/PlexComskip/PlexComskip.py', file_path])


def transcode(file_path):
    print("transcode", file_path)
    return
    try:
        file_name = file_path.split('/')[-1].split('.')[0]
        temp_file = tempfile.NamedTemporaryFile()
        subprocess.check_call(["HandBrakeCLI", "-i", file_path, '-f', 'mkv', '--preset', 'Fast 1080p30', '--optimize',
                               temp_file.name])
        shutil.move(temp_file.name, file_path)
        os.rename(file_path, file_name+'.mkv')
    finally:
        temp_file.close()


def replace_file(src, dest, next_step=None):
    pass


def post_process(grab_path):
    logger.info("post_process started for %s", grab_path)
    plex = PlexPostProcess(BASE_URL, TOKEN)

    file_details = plex.parse_filename(grab_path)
    logger.info("File details %s", file_details)
    item = plex.get_episode(title=file_details['item'],
                            search_file=grab_path.split('/')[-1])
    logger.info("Found item %s", item)
    file_path = plex.get_item_path(item)
    logger.info("Item has path %s", file_path)

    comskip(file_path)

    transcode(file_path)

