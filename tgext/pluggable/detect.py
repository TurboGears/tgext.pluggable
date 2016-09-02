# -*- coding: utf-8 -*-
import inspect


def detect_model(model):
    if not inspect.isclass(model):
        return False

    if hasattr(model, '__mongometa__'):
        return 'ming'
    elif hasattr(model, '__tablename__'):
        return 'sqlalchemy'

    raise ValueError('Unknown model type')


