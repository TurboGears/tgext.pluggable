import logging

log = logging.getLogger('tgext.pluggable')

try:
    from tg.configuration import milestones
except ImportError:
    milestones = None

if milestones is not None:
    from sqlalchemy.schema import SchemaItem, ForeignKeyConstraint

    class LazyForeignKey(SchemaItem):
        def __init__(self, column, **kw):
            super(LazyForeignKey, self).__init__()
            self.resolved = False
            self.column = column
            self.foreign_key_args = kw

        def _set_parent(self, parent):
            def _resolve_myself():
                log.debug('Resolving LazyForeignKey %s' % self)
                parent.table.append_constraint(ForeignKeyConstraint([parent], [self.column()],
                                                                    **self.foreign_key_args))

            milestones.environment_loaded.register(_resolve_myself)
else:
    import sqlalchemy

    log.warn('TurboGears version < 2.3.1, disabling support for SQLAlchemy 0.9')
    try:
        if sqlalchemy.__version__.startswith('0.9'):
            raise ImportError('Support for SQLAlchemy 0.9 is only available on '
                              'TurboGears 2.3.1 and newer.')
    except:
        pass

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

