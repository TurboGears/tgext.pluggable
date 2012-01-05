import transaction

class PluggedBootstrap(object):
    def __init__(self, module_name, previous_bootstrap, plugin_bootstrap):
        self.module_name = module_name
        self.previous_bootstrap = previous_bootstrap
        self.plugin_bootstrap = plugin_bootstrap

    def __call__(self, command, conf, vars):
        #Call previous bootstrap
        self.previous_bootstrap(command, conf, vars)

        #Call this pluggable app bootstrap
        from sqlalchemy.exc import IntegrityError
        try:
            self.plugin_bootstrap(command, conf, vars)
            transaction.commit()
        except IntegrityError:
            print 'Warning, there was a problem running %s bootstrap, might have already been already performed' % self.module_name
            import traceback
            print traceback.format_exc()
            transaction.abort()
            print 'Continuing with bootstrapping...'


class WebSetupAdapter(object):
    def __init__(self, config, module, options):
        self.config = config
        self.models = module.model
        self.options = options
        self.plugin_bootstrap = module.bootstrap.bootstrap
        self.module_name = module.__name__

    def adapt_bootstrap(self):
        current_bootstrap = self.config['package'].websetup.bootstrap
        current_bootstrap.bootstrap = PluggedBootstrap(self.module_name,
                                                       current_bootstrap.bootstrap,
                                                       self.plugin_bootstrap)
