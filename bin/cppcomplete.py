#!/usr/bin/env python3
import re
import os
import sys
import string
import subprocess

MAN = '/usr/bin/man'

def get_man(thing):

    p = subprocess.Popen(f'{MAN} -P cat {thing}',
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)

    for line in p.stdout.readlines():
        line = re.sub(r'\x08.', '', line.decode(sys.stdout.encoding).rstrip())
        if len(line) == 0:
            continue
        yield line


def get_object_classname(filename, thing):

    declare_regex = re.compile(f'(\S+)[ ]{thing};')

    fh = open(filename, 'r')
    lines = reversed(list(fh))

    for line in lines:
        m = declare_regex.search(line)
        if m is not None:
            return m.group(1)

    return None

def get_class_members(classname):

    disregard = [
        "",
        'constructor',
        'destructor',
    ]

    ignoring = True
    member_regex = re.compile(r'^          ([a-z][a-z_]*[+=<>()]*)[ ]')

    for line in get_man(classname):

        if line.lower().startswith('non-member '):
            break

        if ignoring == True and line.lower().startswith('member functions'):
            ignoring = False

        if ignoring == True:
            continue

        m = member_regex.search(line)

        if m is not None:

            member = m.group(1)

            if member.startswith('operator'):
                continue

            if member in disregard:
                continue

            yield member


def run(filename, thing):

    classname = get_object_classname(filename, thing.strip())

    if classname is None:
        return

    members = get_class_members(classname)

    if members is None:
        return

    for member in members:
        print(f'{thing}.{member}')


if __name__ == '__main__':
    if len(sys.argv) == 3:
        filename = sys.argv[1]
        if not os.path.exists(filename):
            raise Exception(f'No such file: {filename}')
        run(filename, sys.argv[2])
