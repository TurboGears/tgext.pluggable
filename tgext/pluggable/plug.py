import logging, inspect
from adapt_models import ModelsAdapter
from adapt_controllers import ControllersAdapter
from adapt_websetup import WebSetupAdapter
from adapt_statics import StaticsAdapter, PluggedStaticsMiddleware
from utils import call_partial

log = logging.getLogger('tgext.pluggable')

class MissingAppIdException(Exception):
    pass

def init_pluggables(app_config):
    first_init = False
    try:
        plugged = app_config['tgext.pluggable.plugged']
    except KeyError:
        first_init = True
        plugged = app_config['tgext.pluggable.plugged'] = {'appids':{}, 'modules':{}}

    if first_init:
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

    return plugged

def plug(app_config, module_name, appid=None, **kwargs):
    plugged = init_pluggables(app_config)

    options = dict(appid=appid)
    options.update(kwargs)
    
    module = __import__(module_name, globals(), locals(),
                        ['plugme', 'model', 'lib', 'helpers', 'controllers', 'bootstrap', 'public', 'partials'],
                        -1)

    log.info('Plugging %s', module_name)
    module_options = module.plugme(app_config, options)
    if not appid:
        appid = module_options.get('appid')

    if not appid:
        raise MissingAppIdException("Application doesn't provide a default id and none has been provided when plugging it")

    plugged['appids'][appid] = module_name
    plugged['modules'][module_name] = dict(module_name=module_name, module=module, statics=None)

    options['appid'] = appid

    if hasattr(module, 'model') and options.get('plug_models', True):
        models_adapter = ModelsAdapter(app_config, module.model, options)
        app_config.register_hook('startup', models_adapter.adapt_tables)
        app_config.register_hook('startup', models_adapter.init_model)

    if hasattr(module, 'helpers') and options.get('plug_helpers', True):
        try:
            app_helpers = app_config.package.lib.helpers
        except:
            app_helpers = None

        if app_helpers:
            setattr(app_helpers, module_name, module.helpers)

            if module_options.get('global_helpers', False):
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
        app_config.register_hook('startup', websetup_adapter.adapt_bootstrap)

    if hasattr(module, 'public') and options.get('plug_statics', True):
        statics_adapter = StaticsAdapter(app_config, module, options)
        statics_adapter.register_statics(module_name, plugged)

