#!/usr/bin/env python

""" Woo, kegger! """

import time

from rq import Queue, Connection, Worker

import downspout


def work_forever():
	while True:
		with Connection():
			qs = [Queue()]

			w = Worker(qs)
			w.work()
			
		time.sleep(1.0)


if __name__ == '__main__':
	work_forever()
