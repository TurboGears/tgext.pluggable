import inspect
from session_wrapper import TargetAppModel

app_model = TargetAppModel()

class ModelsAdapter(object):
    def __init__(self, config, models, options):
        self.config = config
        self.models = models
        self.options = options

    def _is_table(self, entry):
        return inspect.isclass(entry) and hasattr(entry, '__tablename__')

    def _get_tables(self, model):
        return [entry for name,entry in inspect.getmembers(self.models) if self._is_table(entry)]

    def init_model(self):
        if hasattr(self.models, 'init_model'):
            self.models.init_model(self.config['DBSession'])

    def adapt_tables(self):
        project_DeclarativeBase = self.config['model'].DeclarativeBase

        app_id = self.options['appid']
        for model in self._get_tables(self.models):
            if self.options.get('rename_tables', False) and app_id:
                model.__tablename__ = app_id + '_' + model.__tablename__
                model.__table__.name = model.__tablename__
            model.__table__.tometadata(project_DeclarativeBase.metadata)

def primary_key(model):
    return model.__mapper__.primary_key[0]