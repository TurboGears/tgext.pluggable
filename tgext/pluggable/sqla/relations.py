from sqlalchemy import ForeignKey


class LazyForeignKey(ForeignKey):
    @property
    def _colspec(self):
        return self._original_colspec()

    @_colspec.setter
    def _colspec(self, value):
        self._original_colspec = value


def primary_key(model):
    return model.__mapper__.primary_key[0]

