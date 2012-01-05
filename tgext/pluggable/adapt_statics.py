import os
from paste.urlparser import StaticURLParser

class PluggedStaticsMiddleware(object):
    def __init__(self, app, plugged):
        self.plugged = plugged
        self.app = app

    def __call__(self, environ, start_response):
        path_info = environ.get('PATH_INFO', '')

        if not path_info.startswith('/_pluggable/'):
            return self.app(environ, start_response)

        root_path = path_info.split('/')
        while not root_path[0]:
            root_path.pop(0)
        root_path = root_path[1]

        module_config = self.plugged['modules'].get(root_path)
        if module_config:
            environ['PATH_INFO'] = path_info[len('/_pluggable/'+root_path):]
            return module_config['statics'](environ, start_response)
        else:
            return self.app(environ, start_response)


class StaticsAdapter(object):
    def __init__(self, app_config, module, options):
        self.app_config = app_config
        self.module = module
        self.options = options

        self.public_path = os.path.dirname(module.public.__file__)

    def register_statics(self, module_name, plugged):
        if plugged['modules'][module_name]['statics'] is None:
            plugged['modules'][module_name]['statics'] = StaticURLParser(self.public_path)
