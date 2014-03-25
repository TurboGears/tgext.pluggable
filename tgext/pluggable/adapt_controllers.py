from tg.wsgiapp import TGApp

class ControllersAdapter(object):
    def __init__(self, config, controllers, options):
        self.config = config
        self.controllers = controllers
        self.options = options

    def mount_controllers(self, app):
        root_controller = TGApp().find_controller('root')
        app_id = self.options['appid']
        path = app_id.split('.')
        route = path.pop(0)
        while len(path)>0:
            root_controller = getattr(root_controller, route)
            route = path.pop(0)
        setattr(root_controller, route, self.controllers.RootController())

        return app