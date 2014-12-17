#!/usr/bin/env python

import json
import os

from downspout import utils


def fetch(service, artist):
    try:
        metadata = utils.fetch(service, artist)
        with open('./test.txt', 'w') as f:
            f.write(json.dumps(metadata, sort_keys=True, indent=4))
        return True
    except:
        return False


if __name__ == '__main__':
    print("Derp.")