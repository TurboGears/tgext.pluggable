import importlib.util
from importlib.metadata import PackageNotFoundError, distribution
import os, re

from .._compat import distribution_name

from gearbox.command import TemplateCommand

beginning_letter = re.compile(r"^[^a-z]*")
valid_only = re.compile(r"[^a-z0-9_]")

class QuickstartPluggableCommand(TemplateCommand):
    """Create a new pluggable TurboGears 2 application.

Create a new Turbogears project with this command.

Example usage::

    $ paster quickstart-pluggable yourproject

    """

    def get_description(self):
        return self.__doc__

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        parser.add_argument("name")

        parser.add_argument("-p", "--package",
                            help="package name for the code",
                            dest="package")

        return parser

    def take_action(self, opts):
        if not opts.package:
            package = opts.name.lower()
            package = beginning_letter.sub("", package)
            package = valid_only.sub("", package)
            opts.package = package

        opts.name = distribution_name(opts.name)
        opts.project = opts.name

        try:
            installed_project = distribution(opts.name)
        except PackageNotFoundError:
            pass
        else:
            print('The name "%s" is already in use by' % opts.name)
            print(installed_project.metadata['Name'])
            return

        if importlib.util.find_spec(opts.package) is not None:
            print('The package name "%s" is already in use' % opts.package)
            return

        if os.path.exists(opts.name):
            print('A directory called "%s" already exists. Exiting.' % opts.name)
            return


        self.run_template(opts.name, opts)
        os.chdir(opts.name)
