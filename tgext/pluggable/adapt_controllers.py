from tg.wsgiapp import TGApp
from operator import attrgetter

class ControllersAdapter(object):
    def __init__(self, config, controllers, options):
        self.config = config
        self.controllers = controllers
        self.options = options

    def _resolve_mountpoint(self, app_id):
        root = TGApp().find_controller('root')
        
        try:
            route, name = app_id.rsplit('.', 1)
            mountpoint = attrgetter(route)(root).__class__
        except ValueError:
            mountpoint, name = root, app_id

        return mountpoint, name

    def mount_controllers(self, app):
        app_id = self.options['appid']

        mountpoint, name = self._resolve_mountpoint(app_id)
        setattr(mountpoint, name, self.controllers.RootController())

        return app
