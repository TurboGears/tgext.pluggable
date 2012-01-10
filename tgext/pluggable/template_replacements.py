from functools import partial

from tg import request, response, config
from tg.decorators import Decoration, override_template

def replace_template_hook(remainder, params, output):
    req = request._current_obj()

    try:
        dispatch_state = req._controller_state
    except:
        dispatch_state = req.controller_state

    decoration = Decoration.get_decoration(dispatch_state.method)

    if 'tg.locals' in req.environ:
        content_type, engine, template, exclude_names = decoration.lookup_template_engine(req.environ['tg.locals'])
    else:
        content_type, engine, template, exclude_names = decoration.lookup_template_engine(req)

    replaced_template = config._pluggable_templates_replacements.get(template)
    if replaced_template:
        override_template(dispatch_state.method, replaced_template)

def init_replacements(app_config):
    try:
        templates_replacements = app_config._pluggable_templates_replacements
    except:
        templates_replacements = app_config._pluggable_templates_replacements = {}

    for replaced_template, template in templates_replacements.iteritems():
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

