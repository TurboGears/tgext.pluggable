import sys, tg
from tg.decorators import Decoration
from tg.render import render as tg_render

class PartialCaller(object):
    def resolve(self, path):
        module_name, path = path.split('.', 1)
        module = sys.modules[module_name]

        path, func = path.split(':', 1)

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
            func = config['_pluggable_partials_cache'][path]
        except:
            func = config['_pluggable_partials_cache'][path] = self.resolve(path)

        result = func(**params)
        
        if not isinstance(result, dict):
            return result

        #Expect partials not to expose more than one template
        engine_name, template_name, exclude_names = Decoration.get_decoration(func).engines.values()[0]
        replaced_template = config.get('_pluggable_templates_replacements', {}).get(template_name)
        if replaced_template:
            engine_name, template_name = replaced_template.split(':', 1)
        return tg_render(template_vars=result, template_engine=engine_name, template_name=template_name)

call_partial = PartialCaller()

