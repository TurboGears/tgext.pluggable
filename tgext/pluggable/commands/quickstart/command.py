from __future__ import print_function

import os, re, imp
import pkg_resources

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
        parser = super(QuickstartPluggableCommand, self).get_parser(prog_name)

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

        opts.name = pkg_resources.safe_name(opts.name)
        opts.project = opts.name

        env = pkg_resources.Environment()
        if opts.name.lower() in env:
            print('The name "%s" is already in use by' % opts.name)
            for dist in env[opts.name]:
                print(dist)
                return

        try:
            if imp.find_module(opts.package):
                print('The package name "%s" is already in use' % opts.package)
                return
        except ImportError:
            pass

        if os.path.exists(opts.name):
            print('A directory called "%s" already exists. Exiting.' % opts.name)
            return


        self.run_template(opts.name, opts)
        os.chdir(opts.name)
