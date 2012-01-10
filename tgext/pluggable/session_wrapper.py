class PluggableSession(object):
    """
    Provides a Session wrapper that can be used by pluggable
    applications that will proxy the application session
    when the pluggable application is plugged.
    """

    def __init__(self):
        self.wrapped_session = None

    def configure(self, session):
        self.wrapped_session = session

    def __getattr__(self, item):
        return getattr(self.wrapped_session, item)

class TargetAppModel(object):
    """
    Provides a proxy to the application models,
    it is set up by tgext.pluggable to wrap
    the application models at startup.
    """

    def __init__(self):
        self.wrapped_module = None

    def configure(self, models):
        self.wrapped_module = models

    def __getattr__(self, item):
        return getattr(self.wrapped_module, item)