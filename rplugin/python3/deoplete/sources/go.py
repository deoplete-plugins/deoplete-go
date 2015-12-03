import deoplete.util

from .base import Base

class Source(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'go'
        self.mark = '[go]'
        self.filetypes = ['go']
        self.rank = 100
        self.min_pattern_length = 0
        self.is_bytepos = True

    def get_complete_api(self, findstart):
        self.complete_api = self.vim.vars['deoplete#sources#go']
        if self.complete_api == 'gocode':
            return self.vim.call('gocomplete#Complete', findstart, 0)
        elif self.complete_api == 'vim-go':
            return self.vim.call('go#complete#Complete', findstart, 0)
        else:
            return deoplete.util.error(self.vim, "g:deoplete#sources#go is 'gocode' or 'vim-go'")

    def get_complete_position(self, context):
        return self.get_complete_api(1)

    def gather_candidates(self, context):
        return self.get_complete_api(0)
