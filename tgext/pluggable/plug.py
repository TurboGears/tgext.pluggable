import tg
import logging, inspect, traceback
from adapt_models import ModelsAdapter, app_model
from adapt_controllers import ControllersAdapter
from adapt_websetup import WebSetupAdapter
from adapt_statics import StaticsAdapter, PluggedStaticsMiddleware
from utils import call_partial, plug_url

log = logging.getLogger('tgext.pluggable')

class MissingAppIdException(Exception):
    pass

class AlreadyPluggedException(Exception):
    pass

def init_pluggables(app_config):
    first_init = False
    try:
        plugged = app_config['tgext.pluggable.plugged']
    except KeyError:
        first_init = True
        plugged = app_config['tgext.pluggable.plugged'] = {'appids':{}, 'modules':{}}

    if first_init:
        #Hook Application models
        app_model.configure(app_config['model'])

        #Enable plugged statics
        def enable_statics_middleware(app):
            return PluggedStaticsMiddleware(app, plugged)
        app_config.register_hook('after_config', enable_statics_middleware)

        #Inject call_partial helper if application has helpers
        try:
            app_helpers = app_config.package.lib.helpers
        except:
            app_helpers = None

        if app_helpers:
            app_config._pluggable_partials_cache = {}
            app_helpers.call_partial = call_partial
            app_helpers.plug_url = plug_url

    return plugged

class ApplicationPlugger(object):
    def __init__(self, plugged, app_config, module_name, options):
        super(ApplicationPlugger, self).__init__()
        self.plugged = plugged
        self.app_config = app_config
        self.module_name = module_name
        self.options = options

    def plug(self):
        try:
            self._plug_application(self.app_config, self.module_name, self.options)
        except:
            log.exception('Failed to plug %s' % self.module_name)

    def _plug_application(self, app_config, module_name, options):
        module = __import__(module_name, globals(), locals(),
            ['plugme', 'model', 'lib', 'helpers', 'controllers', 'bootstrap', 'public', 'partials'],
            -1)

        appid = options['appid']

        self.plugged['appids'][appid] = module_name
        self.plugged['modules'][module_name] = dict(appid=appid, module_name=module_name, module=module, statics=None)

        if hasattr(module, 'model') and options.get('plug_models', True):
            models_adapter = ModelsAdapter(app_config, module.model, options)
            models_adapter.adapt_tables()
            models_adapter.init_model()

        if hasattr(module, 'helpers') and options.get('plug_helpers', True):
            try:
                app_helpers = app_config.package.lib.helpers
            except:
                app_helpers = None

            if app_helpers:
                setattr(app_helpers, module_name, module.helpers)

                if options.get('global_helpers', False):
                    for name, impl in inspect.getmembers(module.helpers):
                        if name.startswith('_'):
                            continue

                        if not hasattr(app_helpers, name):
                            setattr(app_helpers, name, impl)
                        else:
                            log.warning('%s helper already existing, skipping it' % name)

        if hasattr(module, 'controllers') and options.get('plug_controller', True):
            controllers_adapter = ControllersAdapter(app_config, module.controllers, options)
            app_config.register_hook('after_config', controllers_adapter.mount_controllers)

        if hasattr(module, 'bootstrap') and options.get('plug_bootstrap', True):
            websetup_adapter = WebSetupAdapter(app_config, module, options)
            websetup_adapter.adapt_bootstrap()

        if hasattr(module, 'public') and options.get('plug_statics', True):
            statics_adapter = StaticsAdapter(app_config, module, options)
            statics_adapter.register_statics(module_name, self.plugged)

def plug(app_config, module_name, appid=None, **kwargs):
    plugged = init_pluggables(app_config)

    if module_name in plugged['modules']:
        raise AlreadyPluggedException('Pluggable application has already been plugged for this application')


    module = __import__(module_name, globals(), locals(), ['plugme'], -1)

    plug_options = dict(appid=appid)
    plug_options.update(kwargs)

    log.info('Plugging %s', module_name)
    module_options = module.plugme(app_config, plug_options)
    if not appid:
        appid = module_options.get('appid')

    if not appid:
        raise MissingAppIdException("Application doesn't provide a default id and none has been provided when plugging it")

    options = dict()
    options.update(module_options)
    options.update(plug_options)
    options['appid'] = appid

    plugger = ApplicationPlugger(plugged, app_config, module_name, options)
    app_config.register_hook('startup', plugger.plug)

def plugged():
    plugged = tg.config.get('tgext.pluggable.plugged', None)
    if not plugged:
        return []

    return plugged['modules'].keys()
