import unittest
import os

from plexdvr.postprocess import PlexPostProcess

BASE_URL = os.environ.get('BASE_URL')
TOKEN = os.environ.get('TOKEN')


class FileNameParseTests(unittest.TestCase):

    def test_regular(self):
        in_file_name = '/data/TV Shows/.grab/aa7001b606692bd67acbf97bacc4046311674b6c/The Amazing World of Gumball (2011) - S05E17 - The Box.ts'
        res = PlexPostProcess.parse_filename(in_file_name)
        self.assertDictEqual({
            'item': 'The Amazing World of Gumball',
            'season': 5,
            'episode': 17,
            'item_type': 'Show',
            'year': 2011,
            'title': 'The Box'
        }, res)

    def test_sports(self):
        in_file_name = '/data/TV Shows/.grab/45291a5bda57e0b0796207ed51b64e41a3c6f97f/Little League Softball (2004) - 2017-08-15 00 00 00 - World Series First Semifinal Teams TBA.ts'  # noqa
        res = PlexPostProcess.parse_filename(in_file_name)
        self.assertDictEqual({
            'item': 'Little League Softball',
            'season': 2017,
            'episode': None,
            'item_type': 'Show',
            'year': 2004,
            'title': 'World Series First Semifinal Teams TBA'
        }, res)

    def test_documentary(self):
        in_file_name = '/data/TV Shows/.grab/6186da961f6e4d2c44b669da800d2a0825b0ca71/The Cars That Made America (2017) - S01E02 - Part 2.ts'  # noqa
        res = PlexPostProcess.parse_filename(in_file_name)
        self.assertDictEqual({
            'item': 'The Cars That Made America',
            'season': 1,
            'episode': 2,
            'item_type': 'Show',
            'year': 2017,
            'title': 'Part 2'
        }, res)

    def test_movie(self):
        in_file_name = '/data/Movies/.grab/dd8a56aa56be41a53d39951ef371743a3c60614c/Boyz N the Hood (1991).ts'
        res = PlexPostProcess.parse_filename(in_file_name)
        self.assertDictEqual({
            'item': 'Boyz N the Hood',
            'season': None,
            'episode': None,
            'item_type': 'Movie',
            'year': 1991,
            'title': None
        }, res)

    def test_news(self):
        in_file_name = '/data/TV Shows/.grab/5a0329d7bb65b968e257b3ea5805e7640d678929/Anderson Cooper 360 (2003) - 2017-08-15 00 00 00 - Episode 08-15.ts'  # noqa
        res = PlexPostProcess.parse_filename(in_file_name)
        self.assertDictEqual({
            'item': 'Anderson Cooper 360',
            'season': 2017,
            'episode': None,
            'item_type': 'Show',
            'year': 2003,
            'title': 'Episode 08-15'
        }, res)


class FetchRecordTests(unittest.TestCase):
    def setUp(self):
        self.plex = PlexPostProcess(BASE_URL, TOKEN)

    def test_regular(self):
        in_file_path = '/data/TV Shows/The Amazing World of Gumball/Season 05/The Amazing World of Gumball (2011) - S05E17 - The Box.ts'  # noqa
        in_file_name = in_file_path.split('/')[-1]
        ep = self.plex.get_episode(title='The Amazing World of Gumball', search_file=in_file_name)
        self.assertEqual('com.plexapp.agents.thetvdb://248482/5/17?lang=en', ep.guid)

        item_path = PlexPostProcess.get_item_path(ep)
        self.assertEqual(in_file_path, item_path)

    def test_sports(self):
        in_file_path = '/data/TV Shows/Little League Softball (2004)/Season 2017/Little League Softball (2004) - 2017-08-15 00 00 00 - World Series First Semifinal Teams TBA.ts'  # noqa
        in_file_name = in_file_path.split('/')[-1]
        ep = self.plex.get_episode(title='Little League Softball', search_file=in_file_name)
        self.assertEqual('com.gracenote.onconnect://episode/EP006732700057', ep.guid)

        item_path = PlexPostProcess.get_item_path(ep)
        self.assertEqual(in_file_path, item_path)

    def test_documentary(self):
        in_file_path = '/data/TV Shows/The Cars That Made America (2017)/Season 01/The Cars That Made America (2017) - S01E02 - Part 2.ts'  # noqa
        in_file_name = in_file_path.split('/')[-1]
        ep = self.plex.get_episode(title='The Cars That Made America', search_file=in_file_name)
        self.assertEqual('com.plexapp.agents.thetvdb://333268/1/2?lang=en', ep.guid)

        item_path = PlexPostProcess.get_item_path(ep)
        self.assertEqual(in_file_path, item_path)

    def test_movie(self):
        in_file_path = '/data/Movies/Boyz N the Hood (1991)/Boyz N the Hood (1991).ts'
        in_file_name = in_file_path.split('/')[-1]
        ep = self.plex.get_episode(title='Boyz N the Hood', search_file=in_file_name)
        self.assertEqual('com.gracenote.tms://movie/MV000333990000', ep.guid)

        item_path = PlexPostProcess.get_item_path(ep)
        self.assertEqual(in_file_path, item_path)

    def test_news(self):
        in_file_path = '/data/TV Shows/Anderson Cooper 360 (2003)/Season 2017/Anderson Cooper 360 (2003) - 2017-08-15 00 00 00 - Episode 08-15.ts'  # noqa
        in_file_name = in_file_path.split('/')[-1]
        ep = self.plex.get_episode(title='Anderson Cooper 360', search_file=in_file_name)
        self.assertEqual('com.gracenote.onconnect://episode/185440/2017-08-15', ep.guid)

        item_path = PlexPostProcess.get_item_path(ep)
        self.assertEqual(in_file_path, item_path)



