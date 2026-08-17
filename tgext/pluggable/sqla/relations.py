import logging

from sqlalchemy.schema import ForeignKeyConstraint, SchemaItem
from tg.configuration import milestones

log = logging.getLogger('tgext.pluggable')


class LazyForeignKey(SchemaItem):
    def __init__(self, column, **kw):
        super().__init__()
        self.column = column
        self.foreign_key_args = kw

    def _set_parent(self, parent, **kw):
        def _resolve_myself():
            log.debug('Resolving LazyForeignKey %s', self)
            parent.table.append_constraint(
                ForeignKeyConstraint([parent], [self.column()], **self.foreign_key_args))

        milestones.environment_loaded.register(_resolve_myself)


def primary_key(model):
    return model.__mapper__.primary_key[0]
