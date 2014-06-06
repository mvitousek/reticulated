#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import cStringIO
import argparse
import os

import paramiko
from jinja2 import environment
from jinja2 import loaders


class TemplateInventoryRenderer(object):

    def __init__(self, template_dir):
        print ("Template_dir: ", type (template_dir))
        loader = loaders.FileSystemLoader(template_dir)
        self.environ = environment.Environment(loader=loader)

    def render(self, template_name, args):
        print("Template_name: ", type(template_name))
        template = self.environ.get_template(template_name)
        return template.render(**args)


def parse(lines):
    print("Lines: ", type(lines))
    config = ''.join(lines)
    fd = cStringIO.StringIO(config)
    parser = paramiko.SSHConfig()
    parser.parse(fd)
    return parser


def get_entries(parser):
    print("Parser: ", type(parser))
    return parser._config


def get_netloc(entry, parser):
    print("Entry: ", type(entry))
    hostname = entry.get('host')[0]
    if hostname == '*':
        return
    port = parser.lookup(hostname).get('port')
    return (hostname, port)


def get_netlocs(lines):
    parser = parse(lines)
    entries = get_entries(parser)
    netlocs = {}
    for entry in entries:
        netloc = get_netloc(entry, parser)
        if not netloc:
            continue
        hostname, port = netloc
        netlocs[hostname] = port
    return netlocs


def execute(lines, args):
    print("Args: ", type(args))
    netlocs = get_netlocs(lines)

    if args.template_file:
        dirpath, filename = os.path.split(args.template_file)
        renderer = TemplateInventoryRenderer(dirpath)
        template_context = dict([
            (hostname, '%s:%s' % (hostname, port))
            for hostname, port in netlocs.items()
        ])
        return renderer.render(filename, template_context)

    return '\n'.join(
        ['%s:%s' % (hostname, port) for hostname, port in netlocs.items()]
    )


def _validate(args):
    pass


def _parse_args():
    description = 'Ansible inventory file generating script'
    ' from OpenSSH configuration file'
    arg_parser = argparse.ArgumentParser(description=description)

    option_t_help = 'Use template file'
    arg_parser.add_argument(
        '-t', '--template-file',
        type=str,
        required=False,
        help=option_t_help,
    )

    args = arg_parser.parse_args()
    _validate(args)

    return args


def main():
    try:
        lines = sys.stdin.readlines()
        args = _parse_args()
        result = execute(lines, args)
        print(result)
    except BaseException as e:
        print('Error: %s' % e, file=sys.stderr)


if __name__ == '__main__':
    main()
