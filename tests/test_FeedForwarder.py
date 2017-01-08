import os
import sys
sys.path.append('..')
from pyfeedstg import FeedForwarder


token = os.environ['TOKEN']
url = 'http://127.0.0.1:8888'
userId = '9429534'


def restoreServer():
    while True:
        forwarder = FeedForwarder(token, url, userId)
        if len(forwarder.feed['entries']) == 4:
            break


def test_FeedForwarder():
    restoreServer()
    forwarder = FeedForwarder(token, url, userId)
    assert len(forwarder.feed['entries']) > 0
    assert forwarder.title == 'Test feed'


def test_FeedForwarder_getUpdates():
    restoreServer()
    forwarder = FeedForwarder(token, url, userId)
    updates = forwarder.getUpdates()
    assert len(updates) > 0
    forwarder.getUpdates()


def test_FeedForwarder_sendEntry():
    restoreServer()
    forwarder = FeedForwarder(token, url, userId)
    updates = forwarder.getUpdates()
    forwarder.sendEntry(updates[0])
