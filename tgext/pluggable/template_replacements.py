import tg
from tg import request
from tg.decorators import Decoration, override_template


def replace_template(app_config, past_template, template):
    try:
        templates_replacements = app_config.get_blueprint_value('_pluggable_templates_replacements')
    except KeyError:
        templates_replacements = {}
        app_config.update_blueprint({'_pluggable_templates_replacements': templates_replacements})
        tg.hooks.register('initialized_config', _init_replacements)

    templates_replacements[past_template] = template


def _replace_template_hook(remainder, params, output):
    req = request._current_obj()

    dispatch_state = req._dispatch_state

    try:
        if req.validation.exception:
            controller = req.validation.error_handler
        else:
            controller = dispatch_state.method
    except (AttributeError, KeyError):
        controller = dispatch_state.method

    decoration = Decoration.get_decoration(controller)

    content_type, engine, template, exclude_names = decoration.lookup_template_engine(req.environ['tg.locals'])[:4]

    replaced_template = tg.config['_pluggable_templates_replacements'].get(template)
    if replaced_template:
        override_template(decoration.controller, replaced_template)


def _init_replacements(app_config, conf=None):
    if conf is None:
        conf = app_config

    templates_replacements = conf['_pluggable_templates_replacements']
    for replaced_template, template in templates_replacements.items():
        if template in conf.get('renderers', []):
            engine, template = template, ''
        elif ':' in template:
            engine, template = template.split(':', 1)
        else:
            engine = conf.get('default_renderer')
        templates_replacements[replaced_template] = '%s:%s' % (engine, template)

    tg.hooks.register('before_render', _replace_template_hook)
