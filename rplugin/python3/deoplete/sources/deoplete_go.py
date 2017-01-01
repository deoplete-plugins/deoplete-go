import os
import re
import platform
import subprocess

from collections import OrderedDict

from .base import Base
from deoplete.util import charpos2bytepos, error, expand, getlines, load_external_module

load_external_module(__file__, 'sources/deoplete_go')
from cgo import cgo
from stdlib import stdlib

try:
    load_external_module(__file__, '')
    from ujson import loads
except ImportError:
    from json import loads

known_goos = (
    'appengine', 'android', 'darwin', 'dragonfly', 'freebsd', 'linux', 'nacl',
    'netbsd', 'openbsd', 'plan9', 'solaris', 'windows')


class Source(Base):

    def __init__(self, vim):
        super(Source, self).__init__(vim)

        self.name = 'go'
        self.mark = '[Go]'
        self.filetypes = ['go']
        self.input_pattern = r'(?:\b[^\W\d]\w*|[\]\)])\.(?:[^\W\d]\w*)?'
        self.rank = 500

    def on_init(self, context):
        vars = context['vars']

        self.gocode_binary = \
            expand(vars.get('deoplete#sources#go#gocode_binary', ''))
        self.package_dot = \
            vars.get('deoplete#sources#go#package_dot', False)
        self.sort_class = \
            vars.get('deoplete#sources#go#sort_class', [])
        self.pointer = \
            vars.get('deoplete#sources#go#pointer', False)
        self.auto_goos = \
            vars.get('deoplete#sources#go#auto_goos', False)
        self.goos = \
            vars.get('deoplete#sources#go#goos', '')
        self.goarch = \
            vars.get('deoplete#sources#go#goarch', '')
        self.sock = \
            vars.get('deoplete#sources#go#gocode_sock', '')
        self.use_cache = \
            vars.get('deoplete#sources#go#use_cache', False)
        self.json_directory = \
            expand(vars.get('deoplete#sources#go#json_directory', ''))
        self.cgo = \
            vars.get('deoplete#sources#go#cgo', False)

        self.loaded_gocode_binary = False
        self.complete_pos = re.compile(r'\w*$|(?<=")[./\-\w]*$')

        if self.pointer:
            self.complete_pos = re.compile(self.complete_pos.pattern + r'|\*$')

        if self.cgo:
            load_external_module(__file__, 'clang')
            import clang.cindex as clang

            self.libclang_path = \
                vars.get('deoplete#sources#go#cgo#libclang_path', '')
            if self.libclang_path == '':
                return

            self.cgo_options = {
                'std':
                    vars.get('deoplete#sources#go#cgo#std', 'c11'),
                'sort_algo':
                    vars.get('deoplete#sources#cgo#sort_algo', None)
            }

            if not clang.Config.loaded and \
                    clang.Config.library_path != self.libclang_path:
                clang.Config.set_library_file(self.libclang_path)
                clang.Config.set_compatibility_check(False)

            # Set 'C.' complete pattern
            self.cgo_complete_pattern = re.compile(r'[^\W\d]*C\.')
            # Create clang.cindex.Index database
            self.index = clang.Index.create(0)
            # initialize in-memory cache
            self.cgo_cache, self.cgo_inline_source = dict(), None

    def get_complete_position(self, context):
        m = self.complete_pos.search(context['input'])
        return m.start() if m else -1

    def gather_candidates(self, context):
        # If enabled self.cgo, and matched self.cgo_complete_pattern pattern
        if self.cgo and self.cgo_complete_pattern.search(context['input']):
            return self.cgo_completion(getlines(self.vim))

        result = self.get_cache(context, getlines(self.vim))
        if result is None:
            bufname = self.vim.current.buffer.name
            result = self.get_complete_result(
                context, getlines(self.vim), bufname)

        try:
            if result[1][0]['class'] == 'PANIC':
                error(self.vim, 'gocode panicked')
                return []

            if self.sort_class:
                class_dict = OrderedDict((x, []) for x in self.sort_class)

            out = []
            sep = ' '

            for complete in result[1]:
                word = complete['name']
                info = complete['type']
                _class = complete['class']
                abbr = str(word + sep + info).replace(' func', '', 1)
                kind = _class

                if _class == 'package' and self.package_dot:
                    word += '.'
                if self.pointer and \
                        str(context['input']
                            [context['complete_position']:]) == '*':
                    word = '*' + word

                candidates = dict(
                    word=word, abbr=abbr, kind=kind, info=info, dup=1
                )

                if not self.sort_class or _class == 'import':
                    out.append(candidates)
                elif _class in class_dict.keys():
                    class_dict[_class].append(candidates)

            if self.sort_class:
                for v in class_dict.values():
                    out += v

            return out
        except Exception:
            return []

    def cgo_completion(self, buffer):
        # No include header
        if cgo.get_inline_source(buffer)[0] == 0:
            return

        count, inline_source = cgo.get_inline_source(buffer)

        # exists 'self.cgo_inline_source', same inline sources and
        # already cached cgo complete candidates
        if self.cgo_inline_source is not None and \
                self.cgo_inline_source == inline_source and \
                self.cgo_cache[self.cgo_inline_source]:
            # Use in-memory(self.cgo_headers) cacahe
            return self.cgo_cache[self.cgo_inline_source]
        else:
            self.cgo_inline_source = inline_source
            # return candidates use libclang-python3
            return cgo.complete(
                self.index, self.cgo_cache, self.cgo_options, count,
                self.cgo_inline_source
            )

    def get_cache(self, context, buffer):
        if not self.use_cache:
            return None

        # get package prefix at current input text
        m = re.findall(r'(?:\b[\w\d]+)(?=\.)', context['input'])
        package = str(m[-1]) if m else ''
        current_import = self.parse_import_package(buffer)
        import_package = [x['package'] for x in current_import]

        if package == '' or package in import_package \
                or package not in stdlib.packages:
            return None

        library = stdlib.packages.get(package)
        import_library = [
            x['library'][0] for x in current_import if package == x['package']
        ]
        result = [0, []]
        for x in library:
            package_json = \
                os.path.join(self.json_directory, x, package + '.json')
            if x not in import_library and os.path.isfile(package_json):
                with open(package_json) as j:
                    result[1] += [x for x in loads(j.read())[1]]

        return result

    def get_complete_result(self, context, buffer, bufname):
        offset = self.get_cursor_offset(context)

        env = os.environ.copy()
        if self.auto_goos:
            name = os.path.basename(os.path.splitext(bufname)[0])
            if '_' in name:
                for part in name.rsplit('_', 2):
                    if part in known_goos:
                        env['GOOS'] = part
                        break
            if 'GOOS' not in env:
                for line in buffer:
                    if line.startswith('package '):
                        break
                    elif not line.startswith('// +build'):
                        continue
                    directives = [
                        x.split(',', 1)[0] for x in line[9:].strip().split()
                    ]
                    if platform.system().lower() not in directives:
                        for plat in directives:
                            if plat in known_goos:
                                env['GOOS'] = plat
                                break
        elif self.goos != '':
            env['GOOS'] = self.goos

        if 'GOOS' in env and env['GOOS'] != platform.system().lower():
            env['CGO_ENABLED'] = '0'

        if self.goarch != '':
            env['GOARCH'] = self.goarch

        args = [self.find_gocode_binary(), '-f=json']
        # basically, '-sock' option for mdempsky/gocode.
        # probably meaningless in nsf/gocode that already run the rpc server
        if self.sock != '' and self.sock in ['unix', 'tcp', 'none']:
            args.append('-sock={}'.format(self.sock))

        args += ['autocomplete', bufname, str(offset)]

        process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            env=env
        )
        stdout_data, stderr_data = process.communicate(
            '\n'.join(buffer).encode()
        )

        return loads(stdout_data.decode())

    def get_cursor_offset(self, context):
        line = self.vim.current.window.cursor[0]
        column = context['complete_position']

        return self.vim.call('line2byte', line) + \
            charpos2bytepos('utf-8', context['input'][: column], column) - 1

    def parse_import_package(self, buffer):
        start = 0
        packages = []

        for line, b in enumerate(buffer):

            if re.match(r'^\s*import \w*|^\s*import \(', b):
                start = line
                continue
            elif re.match(r'\)', b):
                break
            elif line > start:
                package_name = re.sub(r'\t|"', '', b)
                if str(package_name).find(r'/', 0) > 0:
                    full_package_name = str(package_name).split('/', -1)
                    package_name = \
                        full_package_name[len(full_package_name) - 1]
                    library = '/'.join(
                        full_package_name[:len(full_package_name) - 1]
                    ),

                    packages.append(
                        dict(
                            library=library, package=package_name
                        )
                    )
                else:
                    packages.append(dict(library='none', package=package_name))
        return packages

    def find_gocode_binary(self):
        if self.gocode_binary != '' and self.loaded_gocode_binary:
            return self.gocode_binary

        try:
            if os.path.isfile(self.gocode_binary):
                self.loaded_gocode_binary = True
                return self.gocode_binary
            else:
                raise
        except Exception:
            return self.find_binary_path('gocode')

    def find_binary_path(self, path):

        def is_exec(bin_path):
            return os.path.isfile(bin_path) and os.access(bin_path, os.X_OK)

        dirpath, binary = os.path.split(path)
        if dirpath:
            if is_exec(path):
                return path
        else:
            for p in os.environ["PATH"].split(os.pathsep):
                p = p.strip('"')
                binary = os.path.join(p, path)
                if is_exec(binary):
                    return binary
        return error(self.vim, path + ' binary not found')
