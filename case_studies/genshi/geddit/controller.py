#!/usr/bin/env python
import operator, os, sys
import cherrypy

class Root(object):

    def __init__(self, data):
        self.data = data

    @cherrypy.expose
    def index(self):
        return 'Geddit'

def main(filename):
    data = {}

    def _save_data():
        print('Saving...')

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
    print('online')

if __name__ == '__main__':
    main(sys.argv[1])
