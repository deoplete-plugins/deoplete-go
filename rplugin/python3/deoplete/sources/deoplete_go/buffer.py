from deoplete.util import getlines


class Buffer(object):

    def __init__(self, vim):
        self.vim = vim
        self.cache_data = []

    def __len__(self):
        """Return the number of lines contained in a Buffer."""
        return len(self.vim.current.buffer)

    def adjust_index(self, idx, default=None):
        """Convert from python indexing convention to nvim indexing convention."""
        if idx is None:
            return default
        elif idx < 0:
            return idx - 1
        else:
            return idx

    def __getitem__(self, idx):
        """Get a buffer line or slice by integer index.
        Indexes may be negative to specify positions from the end of the
        buffer. For example, -1 is the last line, -2 is the line before that
        and so on.
        When retrieving slices, omiting indexes(eg: `buffer[:]`) will bring
        the whole buffer.
        """
        if not isinstance(idx, slice):
            i = self.adjust_index(idx)
            return getlines(self.vim, i, i)
        start = self.adjust_index(idx.start, 0)
        end = self.adjust_index(idx.stop, -1)
        return getlines(self.vim, start, end)

    def __setitem__(self, idx, item):
        """Replace a buffer line or slice by integer index.
        Like with `__getitem__`, indexes may be negative.
        When replacing slices, omiting indexes(eg: `buffer[:]`) will replace
        the whole buffer.
        """
        if not isinstance(idx, slice):
            i = adjust_index(idx)
            lines = [item] if item is not None else []
            return self.request('nvim_buf_set_lines', i, i + 1, True, lines)
        lines = item if item is not None else []
        start = adjust_index(idx.start, 0)
        end = adjust_index(idx.stop, -1)
        return self.request('buffer_set_lines', start, end, False, lines)

    def __iter__(self):
        """Iterate lines of a buffer.
        This will retrieve all lines locally before iteration starts. This
        approach is used because for most cases, the gain is much greater by
        minimizing the number of API calls by transfering all data needed to
        work.
        """
        lines = getlines(self.vim)
        for line in lines:
            yield line

    def __delitem__(self, idx):
        """Delete line or slice of lines from the buffer.
        This is the same as __setitem__(idx, [])
        """
        self.__setitem__(idx, None)

    def append(self, lines, index=-1):
        """Append a string or list of lines to the buffer."""
        if isinstance(lines, (basestring, bytes)):
            lines = [lines]
        return self.vim.current.buffer.append(index, index, True, lines)

    def mark(self, name):
        """Return (row, col) tuple for a named mark."""
        return self.vim.current.buffer.mark(name)

    def range(self, start, end):
        """Return a `Range` object, which represents part of the Buffer."""
        return self.vim.current.buffer.range(start, end)

    def add_highlight(
            self, hl_group, line, col_start=0, col_end=-1, src_id=-1,
            async=None
    ):
        """Add a highlight to the buffer."""
        if async is None:
            async = (src_id != 0)
        return self.vim.current.buffer.add_highlight(
            src_id, hl_group, line, col_start, col_end, async=async
        )

    def clear_highlight(self, src_id, line_start=0, line_end=-1, async=True):
        """Clear highlights from the buffer."""
        self.vim.current.buffer.clear_highlight(
            src_id, line_start, line_end, async=async
        )

    @property
    def name(self):
        """Get the buffer name."""
        return self.vim.eval("expand('%:p')")

    @property
    def valid(self):
        """Return True if the buffer still exists."""
        return self.vim.current.buffer.valid

    @property
    def number(self):
        """Get the buffer number."""
        return self.vim.current.buffer.number

    @property
    def cache(self):
        """Get the cached current buffer data."""
        if len(self.cache_data) > 0:
            return self.cache_data

    @cache.setter
    def cache(self, data):
        """Cache the current buffer data."""
        self.cache_data = data

    def set_cache(self):
        self.cache = getlines(self.vim)
