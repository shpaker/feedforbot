import falcon
from wsgiref import simple_server


class Server(object):
    def __init__(self, *paths):
        self.rss = []
        self.next = 0
        for path in paths:
            with open(path, 'r', encoding='utf-8') as stream:
                self.rss.append(stream.read())
        print(len(self.rss))

    def on_get(self, req, resp):
        if self.next == 2:
            self.next = 0
        resp.body = self.rss[self.next]
        self.next += 1
        print(self.next)

app = falcon.API()
app.add_route('/', Server("rss1.xml", "rss2.xml"))

httpd = simple_server.make_server('127.0.0.1', 8888, app)
httpd.serve_forever()
