from tg.wsgiapp import TGApp

class ControllersAdapter(object):
    def __init__(self, config, controllers, options):
        self.config = config
        self.controllers = controllers
        self.options = options

    def mount_controllers(self, app):
        root_controller = TGApp().find_controller('root')
        app_id = self.options['appid']

        setattr(root_controller, app_id, self.controllers.RootController())

        return app