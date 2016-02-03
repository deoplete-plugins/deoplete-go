import json
import os
import re
import subprocess

from .base import Base


class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'go'
        self.mark = '[go]'
        self.filetypes = ['go']
        self.input_pattern = r'[^. \t0-9]\.\w*'

    def get_complete_position(self, context):
        m = re.search(r'\w*$', context['input'])
        return m.start() if m else -1

    # Json output and convert vim syntax
    def gather_candidates(self, context):
        source = '\n'.join(self.vim.current.buffer).encode()
        buf_path = self.vim.current.buffer.name
        # TODO(zchee): Convert python code
        offset = self.vim.eval(
            "line2byte(line('.')) + (col('.')-2)"
        )

        process = subprocess.Popen([self.GoCodeBinary(),
                                    '-f=json',
                                    'autocomplete',
                                    buf_path,
                                    str(offset)],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   start_new_session=True)
        process.stdin.write(source)
        stdout_data, stderr_data = process.communicate()
        result = json.loads(stdout_data.decode('utf-8'))

        out = []
        try:
            for complete in result[1]:
                word = complete['name']
                class_type = complete['class']

                if class_type == 'package':
                    word += '.'
                elif class_type == 'func':
                    word += '('
                elif complete['type'] == '[]string':
                    word += '['

                out.append(dict(word=word,
                                abbr=complete['name'],
                                kind='{:5}'.format(class_type) +
                                complete['type'].replace('func', ''),
                                info=complete['type'],
                                icase=1,
                                dup=1
                                ))

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
