#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path

import nose
from nose.tools.trivial import eq_
from collections import namedtuple

from futen.main import get_netlocs, execute


class Test_Main(object):

    def test_get_netlocs(self):
        testfile = path.join(path.dirname(__file__), 'data/ssh.config')
        expect = {'web': '2200', 'app': '2201', 'db': '2202'}
        with open(testfile) as fd:
            eq_(expect, get_netlocs(fd.readlines()))

    def test_template_render(self):
        testfile = path.join(path.dirname(__file__), 'data/ssh.config')
        template = path.join(path.dirname(__file__), 'data/inventory_template')
        expectfile = path.join(path.dirname(__file__), 'data/inventory_expect')
        with open(expectfile) as fd:
            expect = ''.join(fd.readlines())
        with open(testfile) as fd:
            lines = fd.readlines()
            args_mock = namedtuple(
                'ArgumentParserMock',
                ['template_file']
            )(template)
            result = execute(lines, args_mock)
            eq_(result, expect)

if __name__ == '__main__':
    nose.main(argv=['nosetests', '-s', '-v'], defaultTest=__file__)
