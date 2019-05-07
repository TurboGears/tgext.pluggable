import logging, inspect

import tg
try:
    # TG >= 2.4
    from tg import ApplicationConfigurator
    from tg.configurator.base import (ConfigurationComponent,
                                      BeforeConfigConfigurationAction,
                                      ConfigReadyConfigurationAction,
                                      AppReadyConfigurationAction)
except ImportError:
    # TG < 2.4
    class ApplicationConfigurator: pass
    class ConfigurationComponent: pass


from .adapt_models import ModelsAdapter, app_model
from .adapt_controllers import ControllersAdapter
from .adapt_websetup import WebSetupAdapter
from .adapt_statics import StaticsAdapter, PluggedStaticsMiddleware
from .utils import call_partial, plug_url
from .i18n import pluggable_translations_wrapper

log = logging.getLogger('tgext.pluggable')


def plug(app_config, module_name, appid=None, **kwargs):
    if isinstance(app_config, ApplicationConfigurator):
        plugged = PluggablesConfigurationComponent.initialise(app_config)
    else:
        plugged = init_pluggables23(app_config)

    if module_name in plugged['modules']:
        raise AlreadyPluggedException(
            'Pluggable application has already been plugged for this application'
        )

    module = __import__(module_name, globals(), locals(), ['plugme'], 0)

    plug_options = dict(appid=appid)
    plug_options.update(kwargs)

    log.info('Plugging %s', module_name)
    module_options = module.plugme(app_config, plug_options)
    if not appid:
        appid = module_options.get('appid')

    if not appid:
        raise MissingAppIdException(
            "Application doesn't provide a default id and none has been provided when plugging it")

    options = dict()
    options.update(module_options)
    options.update(plug_options)
    options['appid'] = appid

    # prevent the application from starting if a pluggable is someway broken
    def fail_if_failed_to_plug(app):
        if not plugged['modules'][module_name]:
            raise RuntimeError('%s failed. look at the exception logged above' % module_name)

    # Record that the pluggable is getting plugged
    plugged['modules'][module_name] = {}
    plugger = ApplicationPlugger(plugged, app_config, module_name, options)

    if isinstance(app_config, ApplicationConfigurator):
        # TG2.4+
        tg.hooks.register('initialized_config', plugger.plug)
        tg.hooks.register('configure_new_app', fail_if_failed_to_plug)
    else:
        # TG2.3
        app_config.register_hook('startup', plugger.plug)
        app_config.register_hook('configure_new_app', fail_if_failed_to_plug)


class PluggablesConfigurationComponent(ConfigurationComponent):
    """Init pluggables support for TG2.4 and newer"""
    id = "pluggables"

    @classmethod
    def initialise(cls, configurator):
        """Init pluggables support for TG2.4+"""
        try:
            configurator.register(PluggablesConfigurationComponent)
        except KeyError:
            # Already registered
            pass

        # We currently don't support turning on/off
        # translations for pluggables through the .ini file.
        # Only through the app_cfg.py itself.
        # So pluggable_translations_wrapper is registered if
        # i18n.enabled was true in the blueprint.
        try:
            i18n_enabled = configurator.get_blueprint_value('i18n.enabled')
        except KeyError:
            i18n_enabled = False

        if i18n_enabled:
            configurator.get_component('dispatch').register_controller_wrapper(
                pluggable_translations_wrapper
            )

        return configurator.get_blueprint_value('tgext.pluggable.plugged')

    def get_defaults(self):
        return {
            'tgext.pluggable.plugged': SharedPluggedDict(),
            'tgext.pluggable.partials_cache': {}
        }

    def get_actions(self):
        return (
            BeforeConfigConfigurationAction(self._configure),
            ConfigReadyConfigurationAction(self._setup),
            AppReadyConfigurationAction(self._add_middleware),
        )

    def _configure(self, conf, app):
        model = conf.get('model')
        if model is not None:
            app_model.configure(model)

    def _setup(self, conf, app):
        # Inject call_partial helper if application has helpers
        app_helpers = conf.get('helpers')
        if not app_helpers:
            return
        app_helpers.call_partial = call_partial
        app_helpers.plug_url = plug_url

    def _add_middleware(self, conf, app):
        plugged = conf['tgext.pluggable.plugged']
        return PluggedStaticsMiddleware(app, plugged)


def init_pluggables23(app_config):
    """Init pluggables support for TG2.3 and lower"""
    first_init = False
    try:
        plugged = app_config['tgext.pluggable.plugged']
    except KeyError:
        first_init = True
        plugged = app_config['tgext.pluggable.plugged'] = SharedPluggedDict()

    try:
        # TG2.2
        register_tg_hook = app_config.register_hook
    except AttributeError:
        # TG2.3+
        register_tg_hook = tg.hooks.register

    try:
        register_controller_wrapper = app_config.register_controller_wrapper
    except AttributeError:
        def register_controller_wrapper(wrapper):
            register_tg_hook('controller_wrapper', wrapper)

    if first_init:
        # Hook Application models
        if app_config.get('model'):
            app_model.configure(app_config['model'])

        # Enable plugged statics
        def enable_statics_middleware(app):
            return PluggedStaticsMiddleware(app, plugged)
        register_tg_hook('after_config', enable_statics_middleware)
        
        if app_config.get('i18n.enabled'):
            register_controller_wrapper(pluggable_translations_wrapper)

        app_config['tgext.pluggable.partials_cache'] = {}

        # Inject call_partial helper if application has helpers
        def enable_pluggable_helpers(app_helpers):
            if not app_helpers:
                return
            app_helpers.call_partial = call_partial
            app_helpers.plug_url = plug_url
            
        try:
            app_helpers = app_config.package.lib.helpers
        except:
            # helpers is not an attribute of lib, use what the configured app usees.
            register_tg_hook(
                'configure_new_app',
                lambda app: enable_pluggable_helpers(app.config.get('helpers'))
            )
        else:
            # Backward compatible for versions that didn't have configure_new_app
            enable_pluggable_helpers(app_helpers)

    return plugged


class ApplicationPlugger(object):
    def __init__(self, plugged, app_config, module_name, options):
        super(ApplicationPlugger, self).__init__()
        self.plugged = plugged
        self.app_config = app_config
        self.module_name = module_name
        self.options = options

    def plug(self, configurator=None, conf=None):
        try:
            self._plug_application(self.app_config, self.module_name, self.options)
        except:
            log.exception('Failed to plug %s' % self.module_name)

    def _plug_application(self, app_config, module_name, options):
        # In some cases the application is reloaded causing the startup hook to trigger again,
        # avoid plugging things over and over in such case.
        if self.plugged['modules'].get(module_name):
            return

        module = __import__(
            module_name,
            globals(),
            locals(),
            ['plugme', 'model', 'lib', 'helpers', 'controllers', 'bootstrap', 'public', 'partials'],
            0
        )

        appid = options['appid']

        self.plugged['appids'][appid] = module_name
        self.plugged['modules'][module_name] = dict(appid=appid,
                                                    module_name=module_name,
                                                    module=module,
                                                    statics=None)

        if hasattr(module, 'model') and options.get('plug_models', True):
            models_adapter = ModelsAdapter(tg.config, module.model, options)
            models_adapter.adapt_tables()
            models_adapter.init_model()

        if hasattr(module, 'helpers') and options.get('plug_helpers', True):
            enable_global_helpers = options.get('global_helpers', False)
            try:
                app_helpers = app_config.package.lib.helpers
            except:
                tg.hooks.register(
                    'configure_new_app',
                    lambda app: self._plug_helpers(app.config.get('helpers'),
                                                   enable_global_helpers,
                                                   module_name,
                                                   module)
                )
            else:
                # Backward compatible for versions that didn't have configure_new_app
                self._plug_helpers(app_helpers, enable_global_helpers, module_name, module)

        if hasattr(module, 'controllers') and options.get('plug_controller', True):
            controllers_adapter = ControllersAdapter(tg.config, module.controllers, options)
            tg.hooks.register('configure_new_app', controllers_adapter.new_app_created)
            if isinstance(app_config, ApplicationConfigurator):
                # TG2.4
                tg.hooks.register('after_wsgi_middlewares', controllers_adapter.mount_controllers)
            else:
                # TG2.3
                tg.hooks.register('after_config', controllers_adapter.mount_controllers)

        if hasattr(module, 'bootstrap') and options.get('plug_bootstrap', True):
            websetup_adapter = WebSetupAdapter(tg.config, module, options)
            websetup_adapter.adapt_bootstrap()

        if hasattr(module, 'public') and options.get('plug_statics', True):
            statics_adapter = StaticsAdapter(tg.config, module, options)
            statics_adapter.register_statics(module_name, self.plugged)

    def _plug_helpers(self, app_helpers, enable_global_helpers, module_name, module):
        if app_helpers is None:
            return
        setattr(app_helpers, module_name, module.helpers)

        if enable_global_helpers:
            for name, impl in inspect.getmembers(module.helpers):
                if name.startswith('_'):
                    continue

                if not hasattr(app_helpers, name):
                    setattr(app_helpers, name, impl)
                else:
                    log.warning('%s helper already existing, skipping it' % name)


class SharedPluggedDict(object):
    """Dictionary of plugged apps.

    This is shared across all apps made by the same configurator.
    The apps are plugged against a configurator, not against a specific app,
    so the state of plugged apps must be shared across configurator and apps.
    """
    def __init__(self):
        self._data = {'appids':{}, 'modules':{}}
    def __getitem__(self, item):
        return self._data.__getitem__(item)
    def __setitem__(self, key, value):
        return self._data.__setitem__(key, value)


class MissingAppIdException(Exception):
    pass


class AlreadyPluggedException(Exception):
    pass
