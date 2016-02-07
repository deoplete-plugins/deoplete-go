import os
import re
import subprocess
import sys

from .base import Base

from deoplete.util import charpos2bytepos

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ujson_dir = os.path.dirname(current_dir)
    sys.path.insert(0, ujson_dir)
    from ujson import loads
except ImportError:
    import json


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'go'
        self.mark = '[go]'
        self.filetypes = ['go']
        self.input_pattern = r'[^. \t0-9]\.\w*'
        self.rank = 500

        try:
            self.sort_class = self.vim.vars['deoplete#sources#go#sort_class']
        except:
            self.sort_class = None

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

        if self.sort_class is not None:
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
            align_class = self.vim.vars['deoplete#sources#go#align_class']
            package_dot = self.vim.vars['deoplete#sources#go#package_dot']
            for complete in result[1]:
                _class = complete['class']
                word = complete['name']
                info = complete['type']

                if _class != "package" and align_class:
                    abbr = '{:<6}'.format(_class) + complete['name']
                else:
                    abbr = _class + ' ' + word

                if _class == 'package' and package_dot:
                    word += '.'
                if _class == 'func':
                    word = word + '('
                    abbr += str(info).replace('func', '')
                elif _class in ('type', 'var'):
                    abbr += ' ' + complete['type']

                candidates = dict(word=word,
                                  abbr=abbr,
                                  info=info,
                                  dup=1
                                  )
                if self.sort_class is None:
                    out.append(candidates)
                else:
                    class_dict[_class].append(candidates)

            # append with sort by complete['class']
            if self.sort_class is not None:
                for c in self.sort_class:
                    for x in class_dict[c]:
                        out.append(x)

            return out
        except Exception:
            return []

    def GoCodeBinary(self):
        try:
            binary_path = self.vim.vars['deoplete#sources#go#gocode_binary']
            if binary_path:
                if os.path.isfile(binary_path):
                    return binary_path
                else:
                    return None
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
        return None
