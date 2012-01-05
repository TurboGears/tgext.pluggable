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
        try:
            func = tg.config._partials_cache[path]
        except:
            func = tg.config._partials_cache[path] = self.resolve(path)

        result = func(**params)
        
        if not isinstance(result, dict):
            return result

        #Expect partials not to expose more than one template
        engine_name, template_name, exclude_names = Decoration.get_decoration(func).engines.values()[0]
        return tg_render(template_vars=result, template_engine=engine_name, template_name=template_name)

call_partial = PartialCaller()