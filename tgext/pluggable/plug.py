import importlib
import inspect
import logging

import tg
from tg import ApplicationConfigurator
from tg.configurator.base import (AppReadyConfigurationAction,
                                  BeforeConfigConfigurationAction,
                                  ConfigReadyConfigurationAction,
                                  ConfigurationComponent)

from .adapt_controllers import ControllersAdapter
from .adapt_models import ModelsAdapter, app_model
from .adapt_statics import PluggedStaticsMiddleware, StaticsAdapter
from .adapt_websetup import WebSetupAdapter
from .i18n import pluggable_translations_wrapper
from .utils import call_partial, plug_url

log = logging.getLogger('tgext.pluggable')


def plug(app_config, module_name, appid=None, **kwargs):
    plugged = PluggablesConfigurationComponent.initialise(app_config)

    if module_name in plugged['modules']:
        raise AlreadyPluggedException(
            'Pluggable application has already been plugged for this application')

    module = importlib.import_module(module_name)
    plug_options = {'appid': appid, **kwargs}

    log.info('Plugging %s', module_name)
    module_options = module.plugme(app_config, plug_options)
    if not appid:
        appid = module_options.get('appid')

    if not appid:
        raise MissingAppIdException(
            "Application doesn't provide a default id and none has been provided when plugging it")

    options = {**module_options, **plug_options, 'appid': appid}

    # prevent the application from starting if a pluggable is someway broken
    def fail_if_failed_to_plug(app):
        if not plugged['modules'][module_name]:
            raise RuntimeError(f'{module_name} failed. look at the exception logged above')

    # Record that the pluggable is getting plugged
    plugged['modules'][module_name] = {}
    plugger = ApplicationPlugger(plugged, app_config, module_name, options)

    tg.hooks.register('initialized_config', plugger.plug)
    tg.hooks.register('configure_new_app', fail_if_failed_to_plug)


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


def _import_pluggable(module_name):
    """Import a pluggable package and its standard submodules."""
    module = importlib.import_module(module_name)
    for submodule in ('plugme', 'model', 'lib', 'helpers', 'controllers',
                      'bootstrap', 'public', 'partials'):
        if not hasattr(module, submodule):
            try:
                importlib.import_module(f'{module_name}.{submodule}')
            except ModuleNotFoundError:
                pass
    return module


class ApplicationPlugger:
    def __init__(self, plugged, app_config, module_name, options):
        self.plugged = plugged
        self.app_config = app_config
        self.module_name = module_name
        self.options = options

    def plug(self, configurator=None, conf=None):
        try:
            self._plug_application(self.app_config, self.module_name, self.options)
        except Exception:
            log.exception('Failed to plug %s', self.module_name)

    def _plug_application(self, app_config, module_name, options):
        # In some cases the application is reloaded causing the startup hook to trigger again,
        # avoid plugging things over and over in such case.
        if self.plugged['modules'].get(module_name):
            return

        module = _import_pluggable(module_name)

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
            except AttributeError:
                tg.hooks.register(
                    'configure_new_app',
                    lambda app: self._plug_helpers(app.config.get('helpers'),
                                                   enable_global_helpers,
                                                   module_name,
                                                   module)
                )
            else:
                self._plug_helpers(app_helpers, enable_global_helpers, module_name, module)

        if hasattr(module, 'controllers') and options.get('plug_controller', True):
            controllers_adapter = ControllersAdapter(tg.config, module.controllers, options)
            tg.hooks.register('configure_new_app', controllers_adapter.new_app_created)
            tg.hooks.register('after_wsgi_middlewares', controllers_adapter.mount_controllers)

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
                    log.warning('%s helper already existing, skipping it', name)


class SharedPluggedDict:
    """Dictionary of plugged apps.

    This is shared across all apps made by the same configurator.
    The apps are plugged against a configurator, not against a specific app,
    so the state of plugged apps must be shared across configurator and apps.
    """
    def __init__(self):
        self._data = {'appids': {}, 'modules': {}}

    def __getitem__(self, item):
        return self._data.__getitem__(item)

    def __setitem__(self, key, value):
        return self._data.__setitem__(key, value)


class MissingAppIdException(Exception):
    pass


class AlreadyPluggedException(Exception):
    pass
