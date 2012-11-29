from pylons.controllers.util import abort
from tg.wsgiapp import TGApp
import tg

def block_function(*args, **kw):
    abort(404)

class ControllersAdapter(object):
    def __init__(self, config, controllers, options):
        self.config = config
        self.controllers = controllers
        self.options = options

    def mount_controllers(self, app):
        root_controller = TGApp().find_controller('root')
        app_id = self.options['appid']

        setattr(root_controller, app_id, self.controllers.RootController())

        print "Looking for blocked controllers in %s..." % app_id
        blocked_controllers = self.options.get('block_controllers',[])

        for controller in blocked_controllers:
            for name, cont in self.controllers.root.__dict__.items():
                if isinstance(cont, tg.controllers.decoratedcontroller._DecoratedControllerMeta):
                    for n, c in cont.__dict__.items():
                        if hasattr(c, 'decoration') and c.decoration.exposed:
                            if n == controller:
                                print "Blocked '%s' in '%s'" % (n, app_id)
                                c.decoration.hooks['before_validate'] = [block_function]

        return app