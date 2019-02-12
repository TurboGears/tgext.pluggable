import sys, tg
from tg.decorators import Decoration
from tg.render import render as tg_render
from tg.exceptions import HTTPFound
from .detect import detect_model


class PartialCaller(object):
    def resolve(self, path):
        path, func = path.split(':', 1)

        try:
            # Module resolution
            __import__(path)
        except ImportError:
            pass

        # Attribute Resolution
        module_name, path = path.split('.', 1)
        module = sys.modules[module_name]

        current = module
        for step in path.split('.'):
            current = getattr(current, step)

        if hasattr(current, '__bases__'):
            controller = current()
        else:
            controller = current

        func = getattr(controller, func)
        return func

    def __call__(self, path, **params):
        config = tg.config._current_obj()
        try:
            func = config['tgext.pluggable.partials_cache'][path]
        except:
            func = config['tgext.pluggable.partials_cache'][path] = self.resolve(path)

        result = func(**params)

        if not isinstance(result, dict):
            return result

        # Expect partials not to expose more than one template
        available_engines = list(Decoration.get_decoration(func).engines.values())
        engine_name, template_name, exclude_names = available_engines[0][:3]
        replaced_template = config.get('_pluggable_templates_replacements', {}).get(template_name)
        if replaced_template:
            engine_name, template_name = replaced_template.split(':', 1)

        # Avoid placing the doctype declaration in Genshi and Kajiki templates
        render_params = {}
        if engine_name == 'genshi':
            render_params['doctype'] = None
        if engine_name == 'kajiki':
            render_params['is_fragment'] = True

        return tg_render(template_vars=result, template_engine=engine_name,
                         template_name=template_name, **render_params)


call_partial = PartialCaller()


def mount_point(pluggable_name):
    pluggable_info = tg.config['tgext.pluggable.plugged']['modules'][pluggable_name]
    pluggable_path = pluggable_info['appid'].replace('.', '/')
    return '/' + pluggable_path


class DeferredMountPointPath(object):
    def __init__(self, pluggable_name, path):
        self.pluggable_name = pluggable_name
        self.path = path

    def __str__(self):
        return mount_point(self.pluggable_name) + self.path

    def startswith(self, what):
        return str(self).startswith(what)

    def __radd__(self, other):
        return other + str(self)


def plug_url(pluggable_name, path, params=None, lazy=False, qualified=False):
    if not params:
        params = {}

    conditional_options = {}
    if qualified is not False:
        conditional_options['qualified'] = qualified

    if lazy:
        return tg.lurl(DeferredMountPointPath(pluggable_name, path), params=params,
                       **conditional_options)
    else:
        return tg.url(DeferredMountPointPath(pluggable_name, path), params=params,
                      **conditional_options)


def plug_redirect(pluggable_name, path, params=None):
    url = plug_url(pluggable_name, path, params)
    raise HTTPFound(location=url)


def plugged(config=None):
    if config is None:
        config = tg.config

    try:
        try:
            plugged = config.get_blueprint_value('tgext.pluggable.plugged')
        except KeyError:
            plugged = None
    except AttributeError:
        plugged = config.get('tgext.pluggable.plugged', None)

    if not plugged:
        return []

    return plugged['modules'].keys()


def primary_key(model):
    """Returns the primary key of the model, detecting if it's a sqlalchemy model a ming model"""
    model_type = detect_model(model)

    if model_type == 'sqlalchemy':
        from tgext.pluggable.sqla import primary_key as primary_key_sqla
        return primary_key_sqla(model)

    if model_type == 'ming':
        from tgext.pluggable.ming import primary_key as primary_key_ming
        return primary_key_ming(model)


def instance_primary_key(instance, as_string=False):
    """Returns the value of the primary key of the instance"""
    p = getattr(instance, primary_key(instance.__class__).name)
    return p if not as_string else str(p)
