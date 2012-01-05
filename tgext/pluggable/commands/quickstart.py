import os
import re
import pkg_resources
from paste.script import command, templates
from paste.script import create_distro
from tempita import paste_script_template_renderer

class QuickstartPluggableTemplate(templates.Template):
    _template_dir = 'templates/quickstart'
    template_renderer = staticmethod(paste_script_template_renderer)
    summary = 'TurboGears 2. Pluggable Application Template'

beginning_letter = re.compile(r"^[^a-z]*")
valid_only = re.compile(r"[^a-z0-9_]")

class QuickstartPluggableCommand(command.Command):
    """Create a new pluggable TurboGears 2 application.

Create a new Turbogears project with this command.

Example usage::

    $ paster quickstart-pluggable yourproject

    """

    version = pkg_resources.get_distribution('tgext.pluggable').version
    summary = __doc__.splitlines()[0]
    usage = '\n' + __doc__
    group_name = "TurboGears2"
    templates = "quickstart-pluggable-template"

    name = None
    package = None

    parser = command.Command.standard_parser(verbose=True)

    def command(self):
        if self.args:
            self.name = self.args[0]

        while not self.name:
            self.name = raw_input("Enter project name: ")

        if not self.package:
            package = self.name.lower()
            package = beginning_letter.sub("", package)
            package = valid_only.sub("", package)
            while not self.package:
                self.package = raw_input(
                    "Enter package name [%s]: " % package).strip() or package

        self.name = pkg_resources.safe_name(self.name)

        env = pkg_resources.Environment()
        if self.name.lower() in env:
            print 'The name "%s" is already in use by' % self.name,
            for dist in env[self.name]:
                print dist
                return

        import imp
        try:
            if imp.find_module(self.package):
                print 'The package name "%s" is already in use' % self.package
                return
        except ImportError:
            pass

        if os.path.exists(self.name):
            print 'A directory called "%s" already exists. Exiting.' % self.name
            return

        command = create_distro.CreateDistroCommand("create")
        cmd_args = []
        cmd_args.append("--template=quickstart-pluggable-template")
        cmd_args.append(self.name)
        cmd_args.append("package=%s" % self.package)

        command.run(cmd_args)

        os.chdir(self.name)
