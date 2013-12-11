from __future__ import print_function
import logging

try:
    import transaction
except ImportError:
    transaction = None

from .exceptions import DBIntegrityErrors

log = logging.getLogger('tgext.pluggable')


class PluggedBootstrap(object):
    def __init__(self, module_name, previous_bootstrap, plugin_bootstrap):
        self.module_name = module_name
        self.previous_bootstrap = previous_bootstrap
        self.plugin_bootstrap = plugin_bootstrap

    def __call__(self, command, conf, vars):
        if not transaction:
            log.warn('Transaction module not available...')

        #Call previous bootstrap
        self.previous_bootstrap(command, conf, vars)

        #Call this pluggable app bootstrap
        try:
            self.plugin_bootstrap(command, conf, vars)
            transaction and transaction.commit()
        except DBIntegrityErrors:
            log.exception('Warning, there was a problem running %s bootstrap, might have already been already performed', self.module_name)
            transaction and transaction.abort()
            log.error('Continuing with bootstrapping...')


class WebSetupAdapter(object):
    def __init__(self, config, module, options):
        self.config = config
        self.models = module.model
        self.options = options
        self.plugin_bootstrap = module.bootstrap.bootstrap
        self.module_name = module.__name__

    def adapt_bootstrap(self):
        #Import application websetup if not already available
        __import__(self.config['package'].__name__, globals(), locals(), ['websetup'])

        websetup = self.config['package'].websetup

        if callable(websetup.bootstrap):
            parent_bootstrap = websetup.bootstrap
            bootstrap_module = websetup
        else:
            parent_bootstrap = websetup.bootstrap.bootstrap
            bootstrap_module = websetup.bootstrap

        bootstrap_module.bootstrap = PluggedBootstrap(self.module_name,
                                                      parent_bootstrap,
                                                      self.plugin_bootstrap)
