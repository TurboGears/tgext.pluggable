import inspect
from ming.odm.mapper import mapper

class MingModelsSupport(object):
    def is_model(self, entity):
        return inspect.isclass(entity) and hasattr(entity, '__mongometa__')

    def merge_model(self, app_models, model, **kw):
        pass

