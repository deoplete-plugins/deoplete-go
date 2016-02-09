import os
import re
import subprocess
import sys

from .base import Base

from deoplete.util import charpos2bytepos
from deoplete.util import error

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ujson_dir = os.path.dirname(current_dir)
    sys.path.insert(0, ujson_dir)
    from ujson import loads
except ImportError:
    from json import loads


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'go'
        self.mark = '[go]'
        self.filetypes = ['go']
        self.input_pattern = r'(?:\b[^\W\d]\w*|[\]\)])\.(?:[^\W\d]\w*)?'
        self.rank = 500

        self.align_class = self.vim.vars['deoplete#sources#go#align_class']
        self.gocode_binary = self.vim.vars['deoplete#sources#go#gocode_binary']
        self.package_dot = self.vim.vars['deoplete#sources#go#package_dot']
        self.sort_class = self.vim.vars['deoplete#sources#go#sort_class']

    def get_complete_position(self, context):
        m = re.search(r'\w*$', context['input'])
        return m.start() if m else -1

    def gather_candidates(self, context):
        line = self.vim.current.window.cursor[0]
        column = context['complete_position']

        buf = self.vim.current.buffer
        offset = self.vim.call('line2byte', line) + \
            charpos2bytepos(self.vim, context['input'][: column], column) - 1
        source = '\n'.join(buf).encode()

        process = subprocess.Popen([self.GoCodeBinary(),
                                    '-f=json',
                                    'autocomplete',
                                    buf.name,
                                    str(offset)],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   start_new_session=True)
        process.stdin.write(source)
        stdout_data, stderr_data = process.communicate()
        result = loads(stdout_data.decode())

        if not self.sort_class == []:
            # TODO(zchee): Why not work with this?
            #              class_dict = {}.fromkeys(self.sort_class, [])
            class_dict = {
                'package': [],
                'func': [],
                'type': [],
                'var': [],
                'const': [],
            }
        try:
            out = []
            sep = ' '
            for complete in result[1]:
                _class = complete['class']
                word = complete['name']
                info = complete['type']

                if not _class == 'package' and self.align_class:
                    abbr = '{:<6}'.format(_class) + word
                else:
                    abbr = _class + sep + word

                if _class == 'package' and self.package_dot:
                    word += '.'
                if _class == 'func':
                    word = word + '('
                    abbr += str(info).strip('func')
                elif _class in ('type', 'var'):
                    abbr += sep + info

                candidates = dict(word=word,
                                  abbr=abbr,
                                  info=info,
                                  dup=1
                                  )
                if self.sort_class == []:
                    out.append(candidates)
                else:
                    class_dict[_class].append(candidates)

            # append with sort by complete['class']
            if not self.sort_class == []:
                for c in self.sort_class:
                    for x in class_dict[c]:
                        out.append(x)

            return out
        except Exception:
            return []

    def GoCodeBinary(self):
        try:
            if os.path.isfile(self.gocode_binary):
                return self.gocode_binary
            else:
                raise
        except Exception:
            return self.FindBinaryPath('gocode')

    def FindBinaryPath(self, cmd):
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
