import inspect

class SQLAModelsSupport(object):
    def is_model(self, model):
        return inspect.isclass(model) and hasattr(model, '__tablename__')

    def merge_model(self, app_models, model, rename_tables=False, appid=None, **kw):
        if rename_tables and appid:
            model.__tablename__ = appid + '_' + model.__tablename__
            model.__table__.name = model.__tablename__
        model.__table__.tometadata(app_models.DeclarativeBase.metadata)
