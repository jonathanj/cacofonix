class InvalidChangeMetadata(ValueError):
    """
    A change fragment contains invalid metadata.
    """


class FragmentCompilationError(RuntimeError):
    """
    Compiling a change fragment failed.
    """
    def __init__(self, path):
        self.path = path
        RuntimeError.__init__(
            self, 'Failed to process a fragment {}'.format(path))
