import os
import re
import subprocess

from .base import Base

from deoplete.util import charpos2bytepos
from deoplete.util import error
from deoplete.util import load_external_module

load_external_module(__file__, 'sources/deoplete_go')
from clang_index import Clang_Index
from stdlib import stdlib

try:
    load_external_module(__file__, 'ujson')
    from ujson import loads
except ImportError:
    from json import loads


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'go'
        self.mark = '[Go]'
        self.filetypes = ['go']
        self.input_pattern = r'(?:\b[^\W\d]\w*|[\]\)])\.(?:[^\W\d]\w*)?'
        self.rank = 500

        self.complete_pos = None

        self.gocode_binary = \
            self.vim.vars['deoplete#sources#go#gocode_binary']
        self.package_dot = \
            self.vim.vars['deoplete#sources#go#package_dot']
        self.sort_class = \
            self.vim.vars['deoplete#sources#go#sort_class']
        self.pointer = \
            self.vim.vars['deoplete#sources#go#pointer']
        self.use_cache = \
            self.vim.vars['deoplete#sources#go#use_cache']
        self.json_directory = \
            self.vim.vars['deoplete#sources#go#json_directory']
        self.debug_enabled = \
            self.vim.vars.get('deoplete#sources#go#debug', 0)
        self.cgo = \
            self.vim.vars['deoplete#sources#go#cgo']

        if self.cgo:
            self.complete_pos = re.compile(r'\w*$|(?<=")[./\-\w]*$')
            load_external_module(__file__, 'clang')
            import clang.cindex as clang

            self.libclang_path = \
                self.vim.vars.get('deoplete#sources#go#cgo#libclang_path', '')
            self.cgo_std = \
                ['-std',
                 self.vim.vars.get('deoplete#sources#go#cgo#std', 'c11'),
                 '-x', 'c']

            if not clang.Config.loaded:
                clang.Config.set_library_file(self.libclang_path)
                clang.Config.set_compatibility_check(False)

            self.index = clang.Index.create(0)

            self.cgo_cache, self.cgo_headers = dict(), None
        else:
            self.complete_pos = re.compile(r'\w*$|(?<=")[./\-\w]*$')

        if self.pointer:
            self.complete_pos = re.compile(self.complete_pos.pattern + r'|\*$')

    def on_event(self, context):
        if context['event'] == 'BufWinEnter':
            buffer = self.vim.current.buffer
            context['complete_position'] = self.vim.current.window.cursor[1]

            self.get_complete_result(buffer, context, kill=True)

    def get_complete_position(self, context):
        m = self.complete_pos.search(context['input'])
        return m.start() if m else -1

    def gather_candidates(self, context):
        buffer = self.vim.current.buffer

        if self.cgo and re.search(r'[^\W\d]*C\.', context['input']):
            if self.cgo_get_include_header(buffer)[0] == 0:
                pass

            elif self.cgo_headers == self.cgo_get_include_header(buffer)[1]:
                return self.cgo_cache[self.cgo_headers]
            else:
                count, self.cgo_headers = self.cgo_get_include_header(buffer)
                return self.cgo_complete(count, self.cgo_headers)

        result = self.get_cache(context, buffer)
        if result is None:
            result = self.get_complete_result(buffer, context)

        try:
            if result[1][0]['class'] == 'PANIC':
                error(self.vim, 'gocode panicked')
                return []

            if self.sort_class:
                class_dict = {
                    'package': [],
                    'func': [],
                    'type': [],
                    'var': [],
                    'const': [],
                }

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

                candidates = dict(word=word,
                                  abbr=abbr,
                                  kind=kind,
                                  info=info,
                                  menu=self.mark,
                                  dup=1)

                if not self.sort_class or _class == 'import':
                    out.append(candidates)
                else:
                    class_dict[_class].append(candidates)

            # append with sort by complete['class']
            if self.sort_class:
                for c in self.sort_class:
                    for x in class_dict[c]:
                        out.append(x)

            return out
        except Exception:
            return []

    def get_cache(self, context, buffer):
        if not self.use_cache:
            return None

        m = re.findall(r'(?:\b[\w\d]+)(?=\.)', context['input'])
        package = str(m[-1]) if m else ''
        current_import = self.parse_import_package(buffer)
        import_package = [x['package'] for x in current_import]

        if package == '' or package in import_package \
                or package not in stdlib.packages:
            return None

        library = stdlib.packages.get(package)
        import_library = [x['library'][0] for x in current_import
                          if package == x['package']]
        result = [0, []]
        for x in library:
            package_json = \
                os.path.join(self.json_directory, x, package + '.json')
            if x not in import_library and os.path.isfile(package_json):
                with open(package_json) as j:
                    result[1] += [x for x in loads(j.read())[1]]

        return result

    def get_complete_result(self, buffer, context, **kwargs):
        line = self.vim.current.window.cursor[0]
        column = context['complete_position']

        offset = self.vim.call('line2byte', line) + \
            charpos2bytepos(self.vim, context['input'][: column],
                            column) - 1
        source = '\n'.join(buffer).encode()

        process = subprocess.Popen(
            [self.find_gocode_binary(), '-f=json', 'autocomplete', buffer.name,
             str(offset)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True)
        process.stdin.write(source)
        stdout_data, stderr_data = process.communicate()
        if kwargs and kwargs['kill'] is True:
            process.kill
        return loads(stdout_data.decode())

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
                    package_name = full_package_name[len(full_package_name) -
                                                     1]
                    library = '/'.join(full_package_name[:len(
                        full_package_name) - 1]),

                    packages.append(dict(library=library,
                                         package=package_name))
                else:
                    packages.append(dict(library='none', package=package_name))
        return packages

    def cgo_get_include_header(self, buffer):
        headers = []
        count = 0

        for b in buffer:
            m = re.search(r'(^#include\s<[^>]+>)$', b)

            if m:
                headers.append(m.group(1))
                count += 1
            elif re.match(r'^\s*import \"C\"', b):
                break

        return (count, '\n'.join(headers))

    def cgo_parse_candidates(self, result):
        completion = {'dup': 1}
        _type = ""
        word = ""
        placeholder = ""

        for chunk in [x for x in result.string if x.spelling]:
            chunk_spelling = chunk.spelling

            if chunk.isKindTypedText():
                word += chunk_spelling
                placeholder += chunk_spelling
                continue

            elif chunk.isKindResultType():
                _type += chunk_spelling
            else:
                placeholder += chunk_spelling

        completion['word'] = word
        completion['abbr'] = completion['info'] = placeholder

        completion['kind'] = \
            ' '.join([(Clang_Index.kinds[result.cursorKind]
                       if (result.cursorKind in Clang_Index.kinds) else
                       str(result.cursorKind)), _type])

        return completion

    def cgo_complete(self, count, headers):
        files = [('fake.c', headers + """
char CString() {
}
""")]
        # clang.TranslationUnit
        # PARSE_NONE = 0
        # PARSE_DETAILED_PROCESSING_RECORD = 1
        # PARSE_INCOMPLETE = 2
        # PARSE_PRECOMPILED_PREAMBLE = 4
        # PARSE_CACHE_COMPLETION_RESULTS = 8
        # PARSE_SKIP_FUNCTION_BODIES = 64
        # PARSE_INCLUDE_BRIEF_COMMENTS_IN_CODE_COMPLETION = 128
        options = 15

        tu = self.index.parse('fake.c',
                              self.cgo_std,
                              unsaved_files=files,
                              options=options)

        cr = tu.codeComplete('fake.c', (count + 2),
                             1,
                             unsaved_files=files,
                             include_macros=False,
                             include_code_patterns=False,
                             include_brief_comments=False)

        self.cgo_cache[headers] = \
            list(map(self.cgo_parse_candidates, cr.results))
        return self.cgo_cache[headers]

    def find_gocode_binary(self):
        try:
            if os.path.isfile(self.gocode_binary):
                return self.gocode_binary
            else:
                raise
        except Exception:
            return self.find_binary_path('gocode')

    def find_binary_path(self, cmd):

        def is_exec(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(cmd)
        if fpath:
            if is_exec(cmd):
                return cmd
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                binary = os.path.join(path, cmd)
                if is_exec(binary):
                    return binary
        return error(self.vim, 'gocode binary not found')
