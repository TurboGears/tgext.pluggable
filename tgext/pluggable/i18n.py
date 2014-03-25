import gettext as _gettext

import copy
import os
from tg import translator, config
from tg.util import lazify
from tg.i18n import LanguageError

__all__ = ['ugettext', 'ungettext', 'lazy_ugettext', 'lazy_ungettext']


def ugettext(pluggable_name, value):
    tr = _get_translator(pluggable_name)
    return tr.ugettext(value)
lazy_ugettext = lazify(ugettext)


def ungettext(pluggable_name, value):
    tr = _get_translator(pluggable_name)
    return tr.ungettext(value)
lazy_ungettext = lazify(ungettext)


def _get_translator(pluggable_name):
    app_translator = translator._current_obj()

    pluggable_translator = getattr(app_translator, 'pluggable_translator', None)
    if pluggable_translator is None:
        pluggable_translator = copy.copy(app_translator)
        pluggable_translator.add_fallback(_translator_for_pluggable(app_translator,
                                                                    pluggable_name))
        app_translator.pluggable_translator = pluggable_translator

    return pluggable_translator


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