from functools import partial

from tg import request, response, config, tmpl_context
from tg.decorators import Decoration, override_template

def replace_template_hook(remainder, params, output):
    req = request._current_obj()

    try:
        dispatch_state = req._controller_state
    except:
        dispatch_state = req.controller_state

    try:
        if req.validation['exception']:
            controller = req.validation['error_handler']
        else:
            controller = dispatch_state.method
    except (AttributeError, KeyError):
        controller = dispatch_state.method

    decoration = Decoration.get_decoration(controller)

    if 'tg.locals' in req.environ:
        content_type, engine, template, exclude_names = decoration.lookup_template_engine(req.environ['tg.locals'])[:4]
    else:
        content_type, engine, template, exclude_names = decoration.lookup_template_engine(req)[:4]

    replaced_template = config._pluggable_templates_replacements.get(template)
    if replaced_template:
        override_template(decoration.controller, replaced_template)

def init_replacements(app_config):
    try:
        templates_replacements = app_config._pluggable_templates_replacements
    except:
        templates_replacements = app_config._pluggable_templates_replacements = {}

    for replaced_template, template in templates_replacements.items():
        if template in app_config.get('renderers', []):
            engine, template = template, ''
        elif ':' in template:
            engine, template = template.split(':', 1)
        else:
            engine = app_config.get('default_renderer')
        templates_replacements[replaced_template] = '%s:%s' % (engine, template)

    app_config.register_hook('before_render', replace_template_hook)

def replace_template(app_config, past_template, template):
    try:
        templates_replacements = app_config._pluggable_templates_replacements
    except:
        templates_replacements = app_config._pluggable_templates_replacements = {}
        app_config.register_hook('startup', partial(init_replacements, app_config))

    templates_replacements[past_template] = template

