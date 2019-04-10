from functools import partial
import logging
import os
import pkg_resources
import tg

log = logging.getLogger('tgext.pluggable')

_etree = None
_cssselect = None
_html = None

class MissingPropertyError(Exception):
    pass

class InvalidActionError(Exception):
    pass

class Patch(object):
    def __init__(self, template):
        if template is None or not template.strip():
            raise MissingPropertyError('template missing for patch')
        self.template = template
        self.actions = []

    def add_action(self, action):
        self.actions.append(action)

    def __repr__(self):
        return '<patch template="%s">%s</patch>' % (self.template, ''.join((repr(a) for a in self.actions)))

class Action(object):
    VALID_ACTIONS = ('replace', 'append', 'prepend', 'content')

    def __init__(self, name, selector, template):
        if name not in Action.VALID_ACTIONS:
            raise InvalidActionError('action is not one of the recognized actions: %s' % Action.VALID_ACTIONS)

        if selector is None or not selector.strip():
            raise MissingPropertyError('sector missing for action %s' % name)

        if template is not None and not template.strip():
            template = None

        self.name = name
        self.selector = _cssselect.CSSSelector(selector)
        self.template = template

    def apply(self, node, content):
        if content:
            content = _etree.fromstring(content)
        else:
            content = None

        getattr(self, '_perform_%s' % self.name)(node, content)

    def _perform_prepend(self, node, content):
        if content is not None:
            node.addprevious(content)

    def _perform_append(self, node, content):
        if content is not None:
            node.addnext(content)

    def _perform_replace(self, node, content):
        if content is not None:
            node.addprevious(content)
        parent = node.getparent()
        if parent is not None:
            parent.remove(node)

    def _perform_content(self, node, content):
        node.text = None
        for child in list(node):
            node.remove(child)
        if content is not None:
            node.append(content)

    def __repr__(self):
        return '<%s selector="%s" template="%s"/>' % (self.name, self.selector, self.template)

def template_patches_store_data(remainder, params, output, *args, **kw):
    tg.request._template_patches_data = output

def template_patches_hook(response, *args, **kw):
    patched_template = response.get('template_name')
    if patched_template is None:
        return

    patches = tg.config._pluggable_templates_patches
    template_patches = patches.get(patched_template)
    if template_patches is None:
        return

    root = _html.document_fromstring(response['response'])
    for patch in template_patches:
        for action in patch.actions:
            nodes = action.selector(root)
            if nodes:
                if action.template is not None:
                    content = tg.render_template(tg.request._template_patches_data, action.engine, action.template)
                else:
                    content = ""

            for node in nodes:
                action.apply(node, content)

    response['response'] = _html.tostring(root, doctype=root.getroottree().docinfo.doctype)

def init_template_patches(app_config, conf=None):
    _import_etree()

    if conf is None:
        # Compatibility with TG <= 2.3
        conf = app_config

    patches = conf['_pluggable_templates_patches']
    for replaced_template, patches_list in patches.items():
        for patch in patches_list:
            for action in patch.actions:
                template = action.template
                if template is None:
                    engine, template = None, None
                elif template in conf.get('renderers', []):
                    engine, template = template, ''
                elif ':' in template:
                    engine, template = template.split(':', 1)
                else:
                    engine = conf.get('default_renderer')
                action.engine = engine
                action.template = template

    try:  # TG2.3
        app_config.register_hook('before_render', template_patches_store_data)
        app_config.register_hook('after_render', template_patches_hook)
    except AttributeError:  # TG2.4+
        tg.hooks.register('before_render', template_patches_store_data)
        tg.hooks.register('after_render', template_patches_hook)
        
def _import_etree():
    global _etree, _cssselect, _html
    if _etree is None:
        try:
            from lxml import html as _html
            from lxml import etree as _etree
        except ImportError:
            log.error('Template patching requires lxml, please install lxml before using it')

        try:
            from lxml import cssselect as _cssselect
        except ImportError:
            log.error('Template patching requires cssselect, please install cssselect before using it')

def _parse_patchfile(patches, patches_file):
    _import_etree()
    log.info('Loading Patches: %s' % patches_file)

    current_patch = None
    context = _etree.iterparse(patches_file, events=('start',))
    for step, elem in context:
        if elem.tag == 'patch':
            current_patch = Patch(elem.get('template'))
            patches.setdefault(current_patch.template, []).append(current_patch)
        elif elem.tag in Action.VALID_ACTIONS and current_patch is not None:
            current_patch.add_action(Action(elem.tag, elem.get('selector'), elem.get('template')))

    return patches

def load_template_patches(app_config, module_name=None):
    if module_name is None:
        try:  # TG>=2.4
            module_name = app_config.get_blueprint_value('package').__name__
        except AttributeError:  # TG<=2.3
            module_name = app_config.package.__name__
    try:
        patches_file = os.path.join(pkg_resources.get_distribution(module_name).location, 'template_patches.xml')
    except pkg_resources.DistributionNotFound:
        log.error('%s module not installed...' % module_name)
        return

    if not os.path.exists(patches_file):
        log.warn('%s module provides no patches file, %s' % (module_name, patches_file))

    try: # TG>=2.4
        patches = app_config.get_blueprint_value('_pluggable_templates_patches')
    except KeyError:
        patches = {}
        app_config.update_blueprint({'_pluggable_templates_patches': patches})
    except AttributeError:  # TG<=2.3
        try:
            patches = app_config._pluggable_templates_patches
        except:
            patches = app_config._pluggable_templates_patches = {}

    _parse_patchfile(patches, patches_file)

    try:  # TG2.3
        app_config.register_hook('startup', partial(init_template_patches, app_config))
    except AttributeError:  # TG2.4+
        tg.hooks.register('initialized_config', init_template_patches)

