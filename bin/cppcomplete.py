#!/usr/bin/env python3
import re
import os
import sys
import string
import subprocess
import tracemalloc

tracemalloc.start()

MAN = '/usr/bin/man'

class CPPComplete:

    PACKAGE_RE       = r'\w+(?: ::\w+ )*'
    METHOD_CALL_RE   = r'\w+[.]\w+[(][^)]*[)]'
    FUNCTION_CALL_RE = r'\w+[(].*[)]'
    MEMBER_VAR_RE    = r'\w+[.]\w+'

    @classmethod
    def get_man(cls, thing):

        p = subprocess.Popen([MAN, '-P', 'cat', thing],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
        output = []
        for line in p.stdout.readlines():
            line = re.sub(r'\x08.', '', line.decode(sys.stdout.encoding).rstrip())
            if len(line) == 0:
                continue
            if line.startswith('No manual entry for'):
                break
            output.append(line)
        p.wait()
        p.stdout.close()
        return output


    @classmethod
    def search_file(cls, filename, line_number, regexes):

        with open(filename, 'r') as fh:
            line_n = 0
            for line in fh:
                line_n += 1
                if line_n == line_number:
                    break
                for regex in regexes:
                    m = regex.search(line)
                    if m is not None:
                        yield m.groups()


    @classmethod
    def find_first_in_file(cls, filename, line_number, regexes):

        lines = []

        with open(filename, 'r') as fh:
            for line in fh:
                lines.append(line.rstrip())
                if line_number > 0 and len(lines) == line_number:
                    break

        for line_i, line in enumerate(lines):
            line_n = line_i + 1
            for regex in regexes:
                m = regex.search(line)
                if m is not None:
                    return line_n, m.group(1)

        return None, None


    @classmethod
    def find_include(cls, dirname, basename):
        candidates = [
            os.path.join(dirname, basename),
            os.path.join('/var/include', basename),
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        return None


    @classmethod
    def find_usings(cls, filename, line_number):

        usings_regexes = [
            re.compile(r'using \s+ ( \w+ ) \s* ;', re.X|re.M|re.S),
            re.compile(r'using \s+ ( \w+ ) \s* = \s* ({PACKAGE_RE}) \s* ;', re.X|re.M|re.S),
        ]
        usings = cls.search_file(filename, line_number, usings_regexes)

        for using in [u for u in usings]:

            if len(using) == 1:
                yield using[0], using[0]
            else:
                yield using


    @classmethod
    def normalize_with_usings(cls, classname, filename, line_number):

        usings = cls.find_usings(filename, line_number)

        if usings is not None:

            for using in usings:

                if using[0] == classname:
                    return using[1]
                elif cls.symbol_is_in(classname, using[0]):
                    return f'{using[0]}::{classname}'

        return classname


    @classmethod
    def symbol_is_in(cls, symbol, namespace):
        lines = cls.get_man(f'{namespace}::{symbol}')
        return len(lines) > 0


    @classmethod
    def get_expression_classname(cls, filename, line_number, expression):

        dirname = os.path.dirname(filename)

        include_regex = re.compile(r'[#]include \s+ ["]( [^"]+ )["]', re.X|re.M|re.S)

        includes = cls.search_file(filename, line_number, [include_regex])

        for include in [i[0] for i in includes]:
            include_path = cls.find_include(dirname, include)
            if include_path is not None:
                definitions_path = os.path.splitext(include_path)[0] + '.cpp'
                if os.path.exists(definitions_path):
                    classname = cls.get_object_classname(definitions_path, 0, expression)
                else:
                    classname = cls.get_member_classname(include_path, 0, expression)

                if classname is not None:
                    return cls.normalize_with_usings(classname, filename, line_number);

        return None


    @classmethod
    def get_member_classname(cls, filename, line_number, member):

        if '::' in member or '.' in member:
            # TODO Enforce member is within classname scope
            classname, _, member = re.split(r'(::|[.])', member, maxsplit=2)

        member_re = re.sub(r'(\W)', r'[\1]', member)
        member_regex = re.compile(f'(\S+) \s+ {member_re}', re.X|re.M|re.S)

        members = cls.search_file(filename, 0, [member_regex])

        if members is not None:
            members = list(members)
            if len(members) > 0:
                return members[0][0]

        return None


    @classmethod
    def get_object_classname(cls, filename, line_number, thing):

        thing_re = re.sub(r'(\W)', r'[\1]', thing)

        regexes = [
            # thing = some::thing(
            re.compile(f'\W {thing} \s* = \s* ({cls.PACKAGE_RE})[(].+[)];', re.X|re.M|re.S),
            # some::thing thing;
            re.compile(f'({cls.PACKAGE_RE}) \s+ {thing_re} \s* [;{{]', re.X|re.M|re.S),
        ]

        _, classname = cls.find_first_in_file(filename, line_number, regexes)

        if classname is not None:
            return cls.normalize_with_usings(classname, filename, line_number);

        regexes = [
            # auto thing = something;
            re.compile(f'auto \s+ {thing} \s* = \s* (\w+);', re.X|re.M|re.S),
            # auto thing = something();
            re.compile(f'auto \s+ {thing} \s* = \s* ({cls.FUNCTION_CALL_RE});', re.X|re.M|re.S),
            # auto thing = something.get_thing();
            re.compile(f'auto \s+ {thing} \s* = \s* ({cls.METHOD_CALL_RE})', re.X|re.M|re.S),
            # auto thing = something.thing;
            re.compile(f'auto \s+ {thing} \s* = \s* ({cls.MEMBER_VAR_RE});', re.X|re.M|re.S),
        ]

        find_line_n, origin = cls.find_first_in_file(filename, line_number, regexes)

        # print(f'\nthing: {thing}, origin: {origin}, [{line_number}] {filename}')

        if origin is None:
            return None

        if origin is not None:
            if '.' not in origin and '->' not in origin:
                classname = cls.get_object_classname(filename, find_line_n, origin)
            else:
                origin_thing, _, origin_member = re.split(r'(->|[.])', origin, maxsplit=2)

                origin_classname = cls.get_object_classname(filename, find_line_n, origin_thing)

                if origin_classname is not None:

                    origin_thing = f'{origin_classname}::{origin_member}'

                    classname = cls.get_expression_classname(filename, find_line_n, origin_thing)

            if classname is not None:
                return cls.normalize_with_usings(classname, filename, line_number);

        return cls.get_expression_classname(filename, find_line_n, origin)


    @classmethod
    def get_class_members(cls, classname):

        disregard = [
            "",
            'constructor',
            'destructor',
        ]

        ignoring = True
        member_regex = re.compile(r'^          ([a-z][a-z_]*[+=<>()]*)[ ]')

        for line in cls.get_man(classname):

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


    @classmethod
    def search(cls, filename, line_number, thing):

        classname = cls.get_object_classname(filename, line_number, thing.strip())

        if classname is None:
            return

        members = cls.get_class_members(classname)

        if members is not None:
            for member in members:
                print(f'{thing}.{member}')


if __name__ == '__main__':
    if len(sys.argv) == 4:
        filename = sys.argv[1]
        if not os.path.exists(filename):
            raise Exception(f'No such file: {filename}')
        if not sys.argv[2].isdigits():
            raise Exception(f'Not a line number: {sys.argv[2]}')
        CPPComplete.search(filename, sys.argv[2], sys.argv[3])
