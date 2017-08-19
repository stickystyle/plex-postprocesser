#!/usr/bin/env python
import re
import datetime
import time
import subprocess
import tempfile
import os
import shutil
import logging

from rq import Queue
from redis import StrictRedis

from plexapi.server import PlexServer

BASE_URL = os.getenv('BASE_URL')
TOKEN = os.getenv('TOKEN')
RQ_TIMEOUT = os.getenv("RQ_TIMEOUT", "6h")
RQ_REDIS_URL = os.getenv("RQ_REDIS_URL", "redis://localhost:6379")
HB_PRESET = os.getenv("HB_PRESET", "Fast 1080p30")

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

r = StrictRedis().from_url(url=RQ_REDIS_URL)

transcode_queue = Queue('transcode', connection=r)


class PlexPostProcess(object):
    def __init__(self, baseurl, token):
        logger.info("Init PlexServer @ '%s'", baseurl)
        self.plex = PlexServer(baseurl, token)

    @staticmethod
    def parse_filename(file_name):
        res = dict(item=None, season=None, episode=None, item_type=None, year=None, title=None)
        title_episode = re.search(
            "\.grab/\w+/(?P<item>.*)\((?P<year>\d+)\)(\s-\s(?P<episode>.*)\s-\s(?P<title>.*))?\.\w+", file_name)
        if title_episode:
            logger.debug("'%s' is Show", file_name)
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
                logger.debug("'%s' is Movie", file_name)
                # Movie
                res['item_type'] = 'Movie'
        return res

    @staticmethod
    def get_item_path(item):
        for part in item.iterParts():
            if "Plex Versions" in part.file:
                logger.debug("'%s' is a plex version", part.file)
                continue
            if os.path.isfile(part.file):
                logger.info("The file for %s is '%s'", item, part.file)
                return part.file

    def get_episode(self, title, search_file):
        logger.info("Searching for '%s' with filename '%s'", title, search_file)
        search_res = self.plex.library.search(title=title)
        logger.info("Found matching items %s", search_res)
        if not search_res:
            logger.error("Did not find an item for %s with filename '%s'", title, search_file)
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
    # TODO: Refactor PlexComskip into a project module for more control
    # TODO: Add config option that allows custom comskip.ini file per show / network
    logger.info("Running comskip on '%s'", file_path)
    subprocess.check_call(['python', '/opt/PlexComskip/PlexComskip.py', file_path])


def transcode(file_path, genres):
    # TODO: Validate that the resulting file is smaller than the source, just like PlexComSkip
    logger.info("Running transcode on '%s'", file_path)
    file_base, file_name = os.path.split(file_path)
    tmpdir = tempfile.mkdtemp()
    out_file = "{}/{}.mp4".format(tmpdir, file_name.split('.')[0:-1])
    logger.info("Writing output to '%s'", out_file)
    
    cmd = ["HandBrakeCLI", "-i", file_path, '-f', 'mkv', '--preset', HB_PRESET, '--optimize',
           '-o', out_file]

    if 'Animation' in genres:
        logger.info("Adding x264 animation tune")
        cmd.extend(['--encoder-tune', 'animation'])
    logger.debug("Executing HB with the command %s", cmd)

    subprocess.check_call(cmd)
    logger.info("moving '%s' to '%s'", out_file, file_base)
    shutil.move(out_file, file_base)
    logger.info("removing '%s'", file_path)
    os.remove(file_path)


def remux(file_path):
    logger.info("Running remux on '%s'", file_path)
    file_base, file_name = os.path.split(file_path)
    tmpdir = tempfile.mkdtemp()
    out_file = "{}/{}.mp4".format(tmpdir, file_name.split('.')[0:-1])
    logger.info("Writing output to '%s'", out_file)

    cmd = ['ffmpeg', '-i', file_path, '-c', 'copy', '-map', '0', out_file]

    subprocess.check_call(cmd)
    logger.info("moving '%s' to '%s'", out_file, file_base)
    shutil.move(out_file, file_base)
    logger.info("removing '%s'", file_path)
    os.remove(file_path)


def post_process(grab_path):
    logger.info("post_process started for '%s'", grab_path)
    # Give plex a few seconds to update its DB with the new recording
    time.sleep(3)
    plex = PlexPostProcess(BASE_URL, TOKEN)

    file_details = plex.parse_filename(grab_path)
    logger.info("File details %s", file_details)
    item = plex.get_episode(title=file_details['item'],
                            search_file=grab_path.split('/')[-1])
    logger.info("Found item %s", item)
    file_path = plex.get_item_path(item)
    logger.info("Item has path '%s'", file_path)

    comskip(file_path)

    genres = [x.tag for x in item.show().genres]
    media = item.media[0]
    if media.videoCodec != 'h264':
        transcode_queue.enqueue(transcode, file_path, genres, result_ttl="6h", timeout="6h")
    elif media.container != 'mp4':
        remux(file_path)


