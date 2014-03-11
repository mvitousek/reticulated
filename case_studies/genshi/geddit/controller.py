#!/usr/bin/env python
import operator, os, pickle, sys
import cherrypy

from genshi.template import TemplateLoader
from geddit.model import Link, Comment

loader = TemplateLoader(
    os.path.join(os.path.dirname(__file__), 'templates'),
    auto_reload=True
)

class Root(object):

    def __init__(self, data):
        self.data = data

    @cherrypy.expose
    def index(self):
        tmpl = loader.load('index.html')
        return tmpl.generate(title='Geddit').render('html', doctype='html')


def main(filename):
    link1 = Link(username='joe', url='http://example.org/', title='An example')
    link1.add_comment('jack', 'Bla bla bla')
    link1.add_comment('joe', 'Bla bla bla, bla bla.')
    link2 = Link(username='annie', url='http://reddit.com/', title='The real thing')
    data = {link1.id: link1, link2.id: link2}

    def _save_data():
        print('Saving...')
        # save data back to the pickle file
        fileobj = open(filename, 'wb')
        try:
            pickle.dump(data, fileobj)
        finally:
            fileobj.close()

    cherrypy.engine.subscribe('stop', _save_data)

    cherrypy.config.update({
        'tools.encode.on': True, 'tools.encode.encoding': 'utf-8',
        'tools.decode.on': True,
        'tools.trailing_slash.on': True,
        'tools.staticdir.root': os.path.abspath(os.path.dirname(__file__)),
    })

    cherrypy.quickstart(Root(data), '/', {
        '/media': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'
        }
    })

if __name__ == '__main__':
    main(sys.argv[1])
