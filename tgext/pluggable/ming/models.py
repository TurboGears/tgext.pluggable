from ..detect import detect_model


class MingModelsSupport(object):
    @classmethod
    def is_model(cls, model):
        try:
            return detect_model(model) == 'ming'
        except ValueError:
            return False

    def merge_model(self, app_models, model, **kw):
        pass


def primary_key(entity):
    return entity._id
