import os
import re
import subprocess

from collections import OrderedDict

from .base import Base
from deoplete.util import charpos2bytepos, error, load_external_module

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

    def on_init(self, context):
        vars = context['vars']

        self.gocode_binary = vars.get(
            'deoplete#sources#go#gocode_binary',
            ''
        )
        self.package_dot = vars.get(
            'deoplete#sources#go#package_dot',
            False
        )
        self.sort_class = vars.get(
            'deoplete#sources#go#sort_class',
            []
        )
        self.pointer = vars.get(
            'deoplete#sources#go#pointer',
            False
        )
        self.use_cache = vars.get(
            'deoplete#sources#go#use_cache',
            False
        )
        self.json_directory = vars.get(
            'deoplete#sources#go#json_directory',
            ''
        )
        self.use_on_event = vars.get(
            'deoplete#sources#go#on_event',
            False
        )
        self.cgo = vars.get(
            'deoplete#sources#go#cgo',
            False
        )
        self.debug_enabled = vars.get(
            'deoplete#sources#go#debug',
            False
        )

        self.complete_pos = re.compile(r'\w*$|(?<=")[./\-\w]*$')

        if self.pointer:
            self.complete_pos = re.compile(self.complete_pos.pattern + r'|\*$')

        if self.cgo:
            load_external_module(__file__, 'clang')
            import clang.cindex as clang

            self.libclang_path = vars.get(
                'deoplete#sources#go#cgo#libclang_path',
                ''
            )
            if self.libclang_path == '':
                return
            self.std = vars.get('deoplete#sources#go#cgo#std', 'c11')

            if not clang.Config.loaded or \
                    clang.Config.library_path is not None and \
                    clang.Config.library_path != self.libclang_path:
                clang.Config.set_library_file(self.libclang_path)
                clang.Config.set_compatibility_check(False)

            self.cgo_complete_pattern = re.compile(r'[^\W\d]*C\.')
            # Create clang.cindex.Index database
            self.index = clang.Index.create(0)
            # for inmemory-cache
            self.cgo_cache, self.cgo_inline_source = dict(), None

    def on_event(self, context):
        if self.use_on_event and context['event'] == 'BufRead':
            # Note that dummy execute for make cache
            try:
                buffer = self.vim.current.buffer
                context['complete_position'] = \
                    self.vim.current.window.cursor[1]
                self.get_complete_result(buffer, context, kill=True)
            except Exception:
                # Ignore the error
                pass

    def get_complete_position(self, context):
        m = self.complete_pos.search(context['input'])
        return m.start() if m else -1

    def gather_candidates(self, context):
        buffer = self.vim.current.buffer

        # When enabled cgo option and match the cgo_complete_pattern
        if self.cgo and self.cgo_complete_pattern.search(context['input']):
            # No include header
            if self.cgo_get_inline_source(buffer)[0] == 0:
                pass
            # Use inline-memory(self.cgo_headers) cacahe
            elif self.cgo_inline_source == self.cgo_get_inline_source(buffer)[1]:
                return self.cgo_cache[self.cgo_inline_source]
            # return candidates use libclang-python3
            else:
                count, self.cgo_inline_source = self.cgo_get_inline_source(buffer)
                return self.cgo_complete(count, self.cgo_inline_source)

        result = self.get_cache(context, buffer)
        if result is None:
            result = self.get_complete_result(buffer, context)

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

                candidates = dict(word=word,
                                  abbr=abbr,
                                  kind=kind,
                                  info=info,
                                  dup=1)

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
            charpos2bytepos('utf-8', context['input'][: column],
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

    def cgo_get_inline_source(self, buffer):
        if 'import "C"' not in buffer:
               return (0, '')

        pos_import_c = list(buffer).index('import "C"')
        c_inline = buffer[:pos_import_c]

        if c_inline[len(c_inline) - 1] == '*/':
            comment_start = \
                next(i for i, v in zip(range(len(c_inline) - 1, 0, -1),
                                       reversed(c_inline)) if v == '/*')
            c_inline = c_inline[comment_start + 1:len(c_inline) - 1]

        return (len(c_inline), '\n'.join(c_inline))

    def cgo_parse_candidates(self, result):
        completion = {'dup': 1}
        _type = ""
        word = ""
        placeholder = ""
        sep = ' '

        for chunk in [x for x in result.string if x.spelling]:
            chunk_spelling = chunk.spelling

            # ignore fake.c main(void) function
            if chunk.isKindTypedText() and chunk_spelling != 'main':
                word += chunk_spelling
                placeholder += chunk_spelling
                continue
            elif chunk.isKindResultType():
                _type += chunk_spelling
            else:
                placeholder += chunk_spelling

        completion['word'] = word
        completion['abbr'] = completion['info'] = placeholder + sep + _type

        completion['kind'] = \
            ' '.join([(Clang_Index.kinds[result.cursorKind]
                       if (result.cursorKind in Clang_Index.kinds) else
                       str(result.cursorKind))])

        return completion

    def get_pkgconfig(self, packages):
        out = []
        for pkg in packages:
            flag = os.popen("pkg-config " + pkg + " --cflags --libs").read()
            out += flag.rstrip().split(' ')
        return out

    def cgo_complete(self, line_count, source):
        cgo_pattern = r'#cgo (\S+): (.+)'
        flags = set()
        for key, value in re.findall(cgo_pattern, source):
            if key == 'pkg-config':
                for flag in self.get_pkgconfig(value.split()):
                    flags.add(flag)
            else:
                flags.add('%s=%s' % (key, value))

        cgo_flags = ['-std', self.std, '-x', 'c'] + list(flags)

        fname = 'cgo_inline.c'
        main = """
int main(void) {
}
"""
        template = source + main
        files = [(fname, template)]

        # clang.TranslationUnit
        # PARSE_NONE = 0
        # PARSE_DETAILED_PROCESSING_RECORD = 1
        # PARSE_INCOMPLETE = 2
        # PARSE_PRECOMPILED_PREAMBLE = 4
        # PARSE_CACHE_COMPLETION_RESULTS = 8
        # PARSE_SKIP_FUNCTION_BODIES = 64
        # PARSE_INCLUDE_BRIEF_COMMENTS_IN_CODE_COMPLETION = 128
        options = 15

        # Index.parse(path, args=None, unsaved_files=None, options = 0)
        tu = self.index.parse(fname,
                              cgo_flags,
                              unsaved_files=files,
                              options=options)

        # TranslationUnit.codeComplete(path, line, column, ...)
        cr = tu.codeComplete(fname, (line_count + 2),
                             1,
                             unsaved_files=files,
                             include_macros=False,
                             include_code_patterns=False,
                             include_brief_comments=False)

        # Go string to C string
        #  The C string is allocated in the C heap using malloc.
        #  It is the caller's responsibility to arrange for it to be
        #  freed, such as by calling C.free (be sure to include stdlib.h
        #  if C.free is needed).
        #  func C.CString(string) *C.char
        #
        # Go []byte slice to C array
        #  The C array is allocated in the C heap using malloc.
        #  It is the caller's responsibility to arrange for it to be
        #  freed, such as by calling C.free (be sure to include stdlib.h
        #  if C.free is needed).
        #  func C.CBytes([]byte) unsafe.Pointer
        #
        # C string to Go string
        #  func C.GoString(*C.char) string
        #
        # C data with explicit length to Go string
        #  func C.GoStringN(*C.char, C.int) string
        #
        # C data with explicit length to Go []byte
        #  func C.GoBytes(unsafe.Pointer, C.int) []byte
        self.cgo_cache[source] = [
            {'word': 'CString',
             'abbr': 'CString(string) *C.char',
             'info': 'CString(string) *C.char',
             'kind': 'function',
             'dup': 1},
            {'word': 'CBytes',
             'abbr': 'CBytes([]byte) unsafe.Pointer',
             'info': 'CBytes([]byte) unsafe.Pointer',
             'kind': 'function',
             'dup': 1},
            {'word': 'GoString',
             'abbr': 'GoString(*C.char) string',
             'info': 'GoString(*C.char) string',
             'kind': 'function',
             'dup': 1},
            {'word': 'GoStringN',
             'abbr': 'GoStringN(*C.char, C.int) string',
             'info': 'GoStringN(*C.char, C.int) string',
             'kind': 'function',
             'dup': 1},
            {'word': 'GoBytes',
             'abbr': 'GoBytes(unsafe.Pointer, C.int) []byte',
             'info': 'GoBytes(unsafe.Pointer, C.int) []byte',
             'kind': 'function',
             'dup': 1},
        ]
        self.cgo_cache[source] += \
            list(map(self.cgo_parse_candidates, cr.results))
        return self.cgo_cache[source]

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
        return error(self.vim, cmd + ' binary not found')
