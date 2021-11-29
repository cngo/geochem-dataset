class InvalidDatasetNameError(Exception):
    pass


class ExtraColumnsError(Exception):
    pass


class MissingColumnsError(Exception):
    pass


class IncorrectNumberOfRowsError(Exception):
    def __init__(self, *args, min_count=None, max_count=None):
        self.min_count = min_count
        self.max_count = max_count


class IntegrityError(Exception):
    pass
