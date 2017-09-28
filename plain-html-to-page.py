#!/usr/bin/env python3

import os
from os.path import join

TOP_EXCLUDE = ['temp']
GLOBAL_EXCLUDE = ['./gcc/slides-mailru/plugin/notes/notes.html']

FRONT_MATTER_LINE = '---\n'
FRONT_MATTER = FRONT_MATTER_LINE + FRONT_MATTER_LINE
ANALYTICS = '{% include analytics.html %}'

def file_has_front_matter(path):
    with open(path, 'rt') as in_f:
        first_line = in_f.readline()
        return first_line == FRONT_MATTER_LINE

def convert(path):
    with open(path, 'rt') as in_f:
        data = in_f.read()
    old = '<head>'
    new = '{}\n  {}\n'.format(old, ANALYTICS)
    data = FRONT_MATTER + data.replace(old, new, 1)
    with open(path, 'wt') as out_f:
        out_f.write(data)

def walk_single_top_dir(start):
    for root, dirs, files in os.walk(start):
        for fname in files:
            if os.path.splitext(fname)[1] != '.html':
                continue
            full_name = join(root, fname)
            if full_name in GLOBAL_EXCLUDE:
                continue
            if file_has_front_matter(full_name):
                continue
            convert(full_name)
            print('Converted ' + full_name)

def main():
    top_dir = os.path.dirname(__file__)
    for name in os.listdir(top_dir):
        if name.startswith('_') or name in TOP_EXCLUDE:
            continue
        full_path = join(top_dir, name)
        if os.path.isdir(full_path):
            walk_single_top_dir(full_path)

if __name__ == '__main__':
    main()
