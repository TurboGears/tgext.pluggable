"""
tgext.pluggable migration

gearbox migrate-pluggable command integrate alembic into tgext.pluggable.
"""
from __future__ import print_function

import pkg_resources
from gearbox.command import TemplateCommand
import os, argparse
from tgext.pluggable import plugged
from paste.deploy import loadapp

class TemplateOptions:
    pass

class MigrateCommand(TemplateCommand):
    """Create and apply SQLAlchemy migrations
    Migrations will be managed inside the 'migration/versions' directory

    Usage: gearbox migrate PLUGNAME COMMAND ...
    Use 'gearbox help migrate' to get list of commands and their usage
    """

    def get_description(self):
        return '''Create and apply SQLAlchemy migrations.

Migrations will be managed inside the 'migration/versions' directory
and applied to the database defined by sqlalchemy.url inside the
configuration file.

Create a new migration::

    $ gearbox migrate PLUGNAME create 'Add New Things'

Apply migrations::

    $ gearbox migrate PLUGNAME upgrade

Get current database version::

    $ gearbox migrate PLUGNAME db_version

Downgrade version::

    $ gearbox migrate PLUGNAME downgrade
'''


    def get_parser(self, prog_name):
        parser = super(MigrateCommand, self).get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter

        parser.add_argument("-c", "--config",
                            help='application config file to read (default: development.ini)',
                            dest='config', default="development.ini")

        parser.add_argument('plugname',
                            help='name of the pluggable application for which to apply migration commands')

        subparser = parser.add_subparsers(dest='command')

        init_parser = subparser.add_parser('init', add_help=False,
                                           help='Initializes the pluggable migrations support')

        create_parser = subparser.add_parser('create', add_help=False,
                                             help='Creates a new migration script for the specified pluggable')
        create_parser.add_argument('name')

        db_version_parser = subparser.add_parser('db_version', add_help=False,
                                                 help='Gives the current version of the database for the specified pluggable')

        upgrade_parser = subparser.add_parser('upgrade', add_help=False,
                                              help='Applies migrations of the specified pluggable')
        upgrade_parser.add_argument('version', nargs='?', default='head')

        downgrade_parser = subparser.add_parser('downgrade', add_help=False,
                                                help='Revert migrations of the specified pluggable')
        downgrade_parser.add_argument('version', nargs='?', default='-1')

        test_parser = subparser.add_parser('test', add_help=False,
                                           help='Tests a migration, applies it and then reverts it')

        return parser

    def take_action(self, opts):
        from alembic import command as alembic_commands

        self.alembic_commands = alembic_commands
        name = pkg_resources.safe_name(opts.plugname)

        if opts.command in ('init', 'create'):
            self._perform_appless_action(name, opts)
            return

        pluggables_to_migrate = []
        if name == 'all':
            pluggables_to_migrate.extend(self._detect_loaded_pluggables(opts))
        else:
            pluggables_to_migrate.append(name)

        print('Migrating', ', '.join(pluggables_to_migrate))
        for pluggable in pluggables_to_migrate:
            self._perform_migration(pluggable, opts)

    def command_init(self, opts, pluggable_opts):
        cfg = pluggable_opts['alembic_cfg']
        repository = cfg.get_main_option('script_location')

        template_options = TemplateOptions()
        template_options.__dict__.update(pluggable_opts)
        self.run_template(repository, template_options)

    def command_create(self, opts, pluggable_opts):
        self.alembic_commands.revision(pluggable_opts['alembic_cfg'], opts.name)

    def command_db_version(self, opts, pluggable_opts):
        self.alembic_commands.current(pluggable_opts['alembic_cfg'])

    def command_upgrade(self, opts, pluggable_opts):
        self.alembic_commands.upgrade(pluggable_opts['alembic_cfg'], opts.version)

    def command_downgrade(self, opts, pluggable_opts):
        self.alembic_commands.downgrade(pluggable_opts['alembic_cfg'], opts.version)

    def command_test(self, opts, pluggable_opts):
        self.alembic_commands.upgrade(pluggable_opts['alembic_cfg'], '+1')
        self.alembic_commands.downgrade(pluggable_opts['alembic_cfg'], '-1')

    def _pluggable_tablename(self, pluggable):
        return pluggable.replace('-', '_').replace('.', '_') + '_migrate'

    def _pluggable_repository(self, pluggable):
         try:
             module = __import__(pluggable)
             location = module.__path__[0]
             return os.path.join(location, 'migration')
         except ImportError:
             print("%s - pluggable not found, or not installed" % pluggable)
             return None

    def _detect_loaded_pluggables(self, opts):
        app = loadapp('config:%s' % opts.config, relative_to=os.getcwd())
        return plugged()

    def _perform_migration(self, pluggable, opts):
        from alembic.config import Config

        repository = self._pluggable_repository(pluggable)
        if repository is None or not os.path.exists(repository):
            print("%s - Pluggable does not support migrations" % pluggable)
            return

        tablename = self._pluggable_tablename(pluggable)
        print('\n%s Migrations' % pluggable)
        print("\tRepository '%s'" % repository)
        print("\tConfiguration File '%s'" % opts.config)
        print("\tVersioning Table '%s'" % tablename)

        alembic_cfg = Config(opts.config, ini_section='app:main')
        alembic_cfg.set_main_option('script_location', repository)

        command = getattr(self, 'command_%s' % opts.command)
        command(opts, {'alembic_cfg':alembic_cfg,
                       'tablename':tablename})

    def _perform_appless_action(self, pluggable, opts):
        from alembic.config import Config

        repository = self._pluggable_repository(pluggable)
        if repository is None:
            return

        tablename = self._pluggable_tablename(pluggable)
        print("\n%s Migrations" % pluggable)
        print("\tRepository '%s'" % repository)
        print("\tVersioning Table '%s'" % tablename)

        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", repository)

        command = getattr(self, 'command_%s' % opts.command)
        command(opts, {'alembic_cfg':alembic_cfg,
                       'tablename':tablename})
