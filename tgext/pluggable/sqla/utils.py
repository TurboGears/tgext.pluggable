def is_sqlaclass(obj):
    return hasattr(obj, '__mapper__')
