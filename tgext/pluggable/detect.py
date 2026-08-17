import inspect


def detect_model(model):
    if not inspect.isclass(model):
        return False

    if hasattr(model, '__mongometa__'):
        return 'ming'

    if hasattr(model, '__tablename__'):
        return 'sqlalchemy'

    raise ValueError('Unknown model type')
