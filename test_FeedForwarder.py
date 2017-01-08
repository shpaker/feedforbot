from pyfeedstg import FeedForwarder


token = '303033948:AAERr7AR2WkrBHG_cDd8oabs3MChEBSenLE'
url = 'https://habrahabr.ru/rss/all/'
userId = '9429534'


def test_FeedForwarder():
    forwarder = FeedForwarder(token, url, userId)
    assert len(forwarder.feed['entries']) > 0
    assert forwarder.title is forwarder.feed['feed']['title']


# def test_FeedForwarder_getUpdates():
#     pass


def test_FeedForwarder_sendEntry():
    forwarder = FeedForwarder(token, url, userId)
    forwarder.sendEntry(forwarder.feed['entries'][0])


# def test_Server(self, filename='test_config.yml'):
#     pass
