import fnmatch
import os
from collections import defaultdict

from gearbox.command import Command
from gearbox.commands import patch


class PlugApplicationCommand(Command):
    def get_description(self):
        return 'Adds a pluggable application to current TurboGears app'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        parser.add_argument('appname', metavar='NAME',
                            help="Name of the application that should be plugged")

        return parser

    def take_action(self, opts):
        if not opts.appname.startswith('tgext.') and not opts.appname.startswith('tgapp-'):
            print('Pluggable applications must start with tgapp- or tgext. name')
            return 1

        pyproject = self._find_file('pyproject.toml')
        setup_py = self._find_file('setup.py')
        if pyproject is None and setup_py is None:
            print('Unable to find pyproject.toml or setup.py')
            return 1

        app_cfg = self._find_file('app_cfg.py')
        if app_cfg is None:
            print('Unable to find app_cfg')
            return 1

        patchcmd = patch.PatchCommand(self.app, self.app_args, 'patch')

        if pyproject is not None:
            print(f'Adding dependency to {pyproject}')
            if opts.appname not in self._content(pyproject):
                patchcmd.run(_OptsDict(
                    regex=True,
                    pattern=pyproject,
                    text='dependencies = \\[',
                    addition=f'"{opts.appname}", ',
                    recursive=True
                ))
        else:
            print(f'Adding dependency to {setup_py}')
            if opts.appname not in self._content(setup_py):
                patchcmd.run(_OptsDict(
                    regex=True,
                    pattern=setup_py,
                    text='install_requires.*=.*\\[',
                    addition=f"'{opts.appname}', ",
                    recursive=True
                ))

        print(f'Plugging Module in {app_cfg}')
        if 'from tgext.pluggable import plug' not in self._content(app_cfg):
            self._writeback(app_cfg, self._append_line(
                self._content(app_cfg),
                '\nfrom tgext.pluggable import plug'
            ))

        plugcode = f'plug(base_config, "{self._plugdef(opts.appname)}")'
        if plugcode not in self._content(app_cfg):
            self._writeback(app_cfg, self._append_line(self._content(app_cfg), plugcode))

        print("Remember to rerun 'pip install -e .' and 'gearbox setup-app'!")

    def _find_file(self, pattern):
        for base, _path, files in os.walk('./'):
            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    return os.path.abspath(os.path.join(base, filename))
        return None

    def _append_line(self, content, line):
        if not content.endswith('\n'):
            content += '\n'
        if not line.endswith('\n'):
            line += '\n'
        content += line
        return content

    def _content(self, filepath):
        with open(filepath, 'r') as f:
            return f.read()

    def _writeback(self, filepath, content):
        with open(filepath, 'w') as f:
            f.write(content)

    def _plugdef(self, appname):
        if appname.startswith('tgapp-'):
            return appname[6:]
        return appname


class _OptsDict(defaultdict):
    def __init__(self, **opts):
        super().__init__(lambda: False)
        self.update(opts)

    def __getattr__(self, item):
        return self[item]
