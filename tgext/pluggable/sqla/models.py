from ..detect import detect_model


class SQLAModelsSupport(object):
    @classmethod
    def is_model(cls, model):
        try:
            return detect_model(model) == 'sqlalchemy'
        except ValueError:
            return False

    def merge_model(self, app_models, model, rename_tables=False, appid=None, **kw):
        if rename_tables and appid:
            model.__tablename__ = appid + '_' + model.__tablename__
            model.__table__.name = model.__tablename__
        model.__table__.tometadata(app_models.DeclarativeBase.metadata)
