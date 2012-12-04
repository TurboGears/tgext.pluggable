from functools import partial
import inspect
import sys
from pylons.controllers.util import abort
from tg.controllers.decoratedcontroller import DecoratedController
from tg.util import odict
from tg import config

def block_controller_function(*args, **kw):
    abort(404)

def get_controllers():
    module = config['application_root_module']
    if module not in sys.modules:
        __import__(module)
    return sys.modules[module].RootController

def map_controllers(path, controller, output):
    if inspect.isclass(controller):
        if not issubclass(controller, DecoratedController):
            return
    else:
        if isinstance(controller, DecoratedController):
            controller = controller.__class__
        else:
            return

    exposed_methods = {}
    output[path and path or '/'] = dict(
        controller=controller, exposed_methods=exposed_methods)
    for name, cont in controller.__dict__.items():
        if hasattr(cont, 'decoration') and cont.decoration.exposed:
            exposed_methods[name] = cont
        map_controllers(path + '/' + name, cont, output)


def try_init_blocks(app_config, *args, **kw):
    app_config.register_hook('after_config', partial(init_blocks, app_config))


def init_blocks(app_config, app, *args, **kw):
    try:
        blocked_controllers = app_config._pluggable_blocked_controllers
    except:
        blocked_controllers = app_config._pluggable_blocked_controllers = {}

    controllers = odict()
    for blocked in blocked_controllers.items():
        map_controllers('', get_controllers(), controllers)
        blocked_method = dict(controllers.items()).get(blocked[0])['exposed_methods'].get(blocked[1])
        if blocked_method and hasattr(blocked_method, 'decoration') and blocked_method.decoration.exposed:
            blocked_method.decoration.hooks['before_validate'] = [block_controller_function]
            print "Blocked method '%s' of controller with path '%s'" % (blocked[1], blocked[0])

    return app

def block_controller(app_config, controller, method):
    try:
        blocked_controllers = app_config._pluggable_blocked_controllers
    except:
        blocked_controllers = app_config._pluggable_blocked_controllers = {}
        app_config.register_hook('startup', partial(try_init_blocks, app_config))

    blocked_controllers[controller] = method



