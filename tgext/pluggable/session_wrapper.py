import tg
from tg.caching import cached_property


class LazyProxy(object):
    def __init__(self):
        self._proxied = None

    def configure(self, obj):
        self._proxied = obj

    def __getattr__(self, item):
        return getattr(self._proxied, item)


class PluggableSession(LazyProxy):
    """
    Provides a Session wrapper that can be used by pluggable
    applications that will proxy the application session
    when the pluggable application is plugged.
    """

    def __init__(self):
        super(PluggableSession, self).__init__()
        # This is required for Ming support, should be ignored by SQLAlchemy
        self.impl = LazyProxy()

    def configure(self, session):
        super(PluggableSession, self).configure(session)
        self.impl.configure(getattr(session, 'impl', None))

    @cached_property
    def wrapped_session(self):
        return self._proxied


class TargetAppModel(LazyProxy):
    """
    Provides a proxy to the application models,
    it is set up by tgext.pluggable to wrap
    the application models at startup.
    """
    def plugged(self, pluggable):
        plugged = tg.config.get('tgext.pluggable.plugged', {}).get('modules', {})
        if pluggable in plugged:
            return plugged[pluggable]['module'].model

