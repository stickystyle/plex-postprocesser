#!/usr/bin/env python
import re
import datetime
import subprocess
import tempfile
import os
import shutil

from plexapi.server import PlexServer

BASE_URL = os.environ.get('BASE_URL')
TOKEN = os.environ.get('TOKEN')


class PlexPostProcess(object):
    def __init__(self, baseurl, token):
        self.plex = PlexServer(baseurl, token)

    @staticmethod
    def parse_filename(file_name):
        res = dict(item=None, season=None, episode=None, item_type=None, year=None, title=None)
        title_episode = re.search(
            "\.grab/\w+/(?P<item>.*)\((?P<year>\d+)\)(\s-\s(?P<episode>.*)\s-\s(?P<title>.*))?\.\w+", file_name)
        if title_episode:
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
                # Movie
                res['item_type'] = 'Movie'
        return res

    @staticmethod
    def get_item_path(item):
        for part in item.iterParts():
            if "Plex Versions" in part.file:
                continue
            if os.path.isfile(part.file):
                return part.file

    def get_episode(self, title, search_file):
        print(title, search_file)
        search_res = self.plex.library.search(title=title)
        print(search_res)
        for show in search_res:
            try:
                for episode in show.episodes():
                    print(episode)
                    for part in episode.iterParts():
                        file_name = part.file.split('/')[-1]
                        if file_name == search_file:
                            return episode
            except TypeError:
                for part in show.iterParts():
                    file_name = part.file.split('/')[-1]
                    if file_name == search_file:
                        return show


def comskip(file_path):
    print("comskip", file_path)
    subprocess.check_call(['python', '/opt/PlexComskip/PlexComskip.py', file_path])


def transcode(file_path):
    print("transcode")
    return
    try:
        temp_file = tempfile.NamedTemporaryFile()
        subprocess.check_call(["HandBrakeCLI", "-i", file_path, '-f', 'mkv', '--preset', 'Fast 1080p30', '--optimize',
                               temp_file.name])
        shutil.move(temp_file.name, file_path)
    finally:
        temp_file.close()
    pass


def post_process(grab_path):
    plex = PlexPostProcess(BASE_URL, TOKEN)

    file_details = plex.parse_filename(grab_path)
    print(file_details)
    item = plex.get_episode(title=file_details['item'],
                            search_file=grab_path.split('/')[-1])
    print("found", item)
    file_path = plex.get_item_path(item)

    comskip(file_path)

    transcode(file_path)

