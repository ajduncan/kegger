#!/usr/bin/env python

import json
import os
import sys

from flask.ext.mongoengine import MongoEngine
from downspout import services, utils

from models import Artist, Media, File, db


def fetch(service, artist):
    if service not in services:
        return False

    try:
        metadata = utils.fetch(service, artist)
        db.connect('testing')
        artist_count = Artist.objects(name=artist, service=service).count()
        if not artist_count:
            mongo_artist = Artist(name=artist, service=service).save()
        else:
            mongo_artist = Artist.objects(name=artist, service=service).first()

        for track in metadata[artist]['tracks']:
            track_title = track
            track_album = metadata[artist]['tracks'][track_title]['album']
            track_encoding = metadata[artist]['tracks'][track_title]['encoding']
            track_url = metadata[artist]['tracks'][track_title]['url']
            track_folder = metadata[artist]['tracks'][track_title]['track_folder']
            track_filename = metadata[artist]['tracks'][track_title]['track_filename']

            media_count = Media.objects(artist=mongo_artist, title=track_title).count()
            if not media_count:
                data = open(track_folder + '/' + track_filename, 'rb')
                f = File(name=track_filename, data=data).save()
                media = Media(artist=mongo_artist, title=track_title, data=f).save()

        return True
    except:
        err = sys.exc_info()[0]
        return False


if __name__ == '__main__':
    print("Derp.")