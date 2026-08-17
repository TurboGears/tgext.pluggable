import gettext as _gettext
import os

from tg import config, translator
from tg.i18n import LanguageError

from .utils import plugged


def pluggable_translations_wrapper(next_caller):
    def _add_pluggable_translations(config, controller, remainder, params):
        _add_pluggables_translators()
        return next_caller(config, controller, remainder, params)

    return _add_pluggable_translations


def _add_pluggables_translators():
    app_translator = translator._current_obj()
    for pluggable in plugged():
        app_translator.add_fallback(_translator_for_pluggable(app_translator, pluggable))


def _translator_for_pluggable(app_translator, pluggable_name):
    langs = getattr(app_translator, 'tg_lang', []) or []

    module = config['tgext.pluggable.plugged']['modules'][pluggable_name]['module']
    localedir = os.path.join(os.path.dirname(module.__file__), 'i18n')

    try:
        translator = _gettext.translation(pluggable_name, localedir, languages=langs,
                                          fallback=True)
    except IOError as ioe:
        raise LanguageError('IOError: %s' % ioe)

    return translator
