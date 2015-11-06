import inspect
import logging
from .session_wrapper import TargetAppModel

try:
    from .sqla.models import SQLAModelsSupport
except ImportError:
    pass

try:
    from .ming.models import MingModelsSupport
except ImportError:
    pass

log = logging.getLogger('tgext.pluggable')
app_model = TargetAppModel()

class ModelsAdapter(object):
    def __init__(self, config, models, options):
        self.config = config
        self.models = models
        self.options = options
        self.support = None
        self.tgapp_model = None

        self._init_models_support()

    def _init_models_support(self):
        self.tgapp_model = getattr(self.config['package'], 'model', None)
        if self.tgapp_model is None:
            return

        if self.config.get('use_sqlalchemy'):
            self.support = SQLAModelsSupport()
        elif self.config.get('use_ming'):
            self.support = MingModelsSupport()

    def _get_entities(self, model):
        return [entry for name,entry in inspect.getmembers(self.models) if self.support.is_model(entry)]

    def init_model(self):
        if self.support is None:
            return

        if hasattr(self.models, 'init_model'):
            DBSession = self.config.get('DBSession')
            if DBSession is None:
                log.warn("Pluggable requires a database, but application didn't provide an DBSession property for AppConfig")
                return

            self.models.init_model(DBSession)

    def adapt_tables(self):
        if self.support is None:
            return

        merge_models = self.options.get('global_models', False)
        for model in self._get_entities(self.models):
            if merge_models:
                setattr(self.tgapp_model, model.__name__, model)

            self.support.merge_model(self.tgapp_model, model, **self.options)

