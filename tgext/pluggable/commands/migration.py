"""
tgext.pluggable migration

gearbox sqla-migrate-pluggable command integrate sqlalchemy-migrate into tgext.pluggable.

To start a migration, run command::

    $ gearbox sqla-migrate-pluggable create

And sqla-migrate-pluggable command will create a 'migration' directory for you.
With sqla-migrate-pluggable command you don't need use 'manage.py' in 'migration' directory anymore.

Then you could bind the database with migration with command::

    $ gearbox sqla-migrate-pluggable version_control

Usage:

.. parsed-literal::

   gearbox sqla-migrate-pluggable PLUGNAME help
   gearbox sqla-migrate-pluggable PLUGNAME create
   gearbox sqla-migrate-pluggable PLUGNAME vc|version_control
   gearbox sqla-migrate-pluggable PLUGNAME dbv|db_version
   gearbox sqla-migrate-pluggable PLUGNAME v|version
   gearbox sqla-migrate-pluggable PLUGNAME manage [script.py]
   gearbox sqla-migrate-pluggable PLUGNAME test [script.py]
   gearbox sqla-migrate-pluggable PLUGNAME ci|commit [script.py]
   gearbox sqla-migrate-pluggable PLUGNAME up|upgrade [--version]
   gearbox sqla-migrate-pluggable PLUGNAME downgrade [--version]


check http://code.google.com/p/sqlalchemy-migrate/wiki/MigrateVersioning for detail.

"""
from __future__ import print_function
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

import pkg_resources
from gearbox.command import Command
import os, sys, logging, argparse
from tgext.pluggable import plugged
from paste.deploy import loadapp

class MigrateCommand(Command):
    """Create and apply SQLAlchemy migrations
Migrations will be managed inside the 'migration/versions' directory

Usage: gearbox sqla-migrate-pluggable PLUGNAME COMMAND ...
Use 'gearbox sqla-migrate-pluggable PLUGNAME help' to get list of commands and their usage

Create a new migration::

    $ gearbox sqla-migrate-pluggable PLUGNAME script 'Add New Things'

Apply migrations::

    $ gearbox sqla-migrate-pluggable PLUGNAME upgrade
"""

    def get_description(self):
        return self.__doc__

    def get_parser(self, prog_name):
        parser = super(MigrateCommand, self).get_parser(prog_name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter

        parser.add_argument("-c", "--config",
            help='application config file to read (default: development.ini)',
            dest='ini', default="development.ini")

        parser.add_argument('args', nargs='*')

        return parser

    def _setup_logging(self):
        """
        As we disable the sqlalchemy-migrate logging to avoid writing the same output
        multiple times due to migrate.versioning.shell.main setting up logging each time
        we must configure logging manually the same way sqlalchemy-migrate does
        """

        # filter to log =< INFO into stdout and rest to stderr
        class SingleLevelFilter(logging.Filter):
            def __init__(self, min=None, max=None):
                self.min = min or 0
                self.max = max or 100

            def filter(self, record):
                return self.min <= record.levelno <= self.max

        logger = logging.getLogger()
        h1 = logging.StreamHandler(sys.stdout)
        f1 = SingleLevelFilter(max=logging.INFO)
        h1.addFilter(f1)
        h2 = logging.StreamHandler(sys.stderr)
        f2 = SingleLevelFilter(min=logging.WARN)
        h2.addFilter(f2)
        logger.addHandler(h1)
        logger.addHandler(h2)
        logger.setLevel(logging.INFO)

    def _pluggable_tablename(self, pluggable):
        return pluggable.replace('-', '_').replace('.', '_') + '_migrate'

    def _pluggable_repository(self, pluggable):
        try:
            return os.path.join(pkg_resources.get_distribution(pluggable).location, 'migration')
        except pkg_resources.DistributionNotFound:
            print("%s - pluggable not found" % pluggable)
            return None

    def _detect_loaded_pluggables(self):
        app = loadapp('config:%s' % self.options.ini, relative_to=os.getcwd())
        return plugged()

    def _perform_migration(self, pluggable):
        from migrate.versioning.shell import main

        repository = self._pluggable_repository(pluggable)
        if repository is None or not os.path.exists(repository):
            print("%s - Pluggable does not support migrations" % pluggable)
            return

        tablename = self._pluggable_tablename(pluggable)
        print('\n%s Migrations' % pluggable)
        print("\tRepository '%s'" % repository)
        print("\tDatabase '%s'" % self.dburi)
        print("\tVersioning Table '%s'" % tablename)

        #disable logging, this is due to sqlalchemy-migrate bug that
        #causes the disable_logging option to ignored
        args = self.args[:1] + ['-q'] + self.args[1:]

        main(argv=args, url=self.dburi, repository=repository, name=pluggable,
             version_table=tablename, disable_logging=True)

    def _perform_appless_action(self, pluggable):
        from migrate.versioning.shell import main

        repository = self._pluggable_repository(pluggable)
        if repository is None:
            return

        tablename = self._pluggable_tablename(pluggable)
        print("\n%s Migrations" % pluggable)
        print("\tRepository '%s'" % repository)
        print("\tVersioning Table '%s'" % tablename)

        #disable logging, this is due to sqlalchemy-migrate bug that
        #causes the disable_logging option to ignored
        args = self.args[:1] + ['-q'] + self.args[1:]

        main(argv=args, url=None, repository=repository, name=pluggable,
             version_table=tablename, disable_logging=True)

    def take_action(self, opts):
        #Work-around for SQLA0.8 being incompatible with sqlalchemy-migrate
        import sqlalchemy
        sqlalchemy.exceptions = sqlalchemy.exc

        from migrate.versioning.shell import main
        from migrate.exceptions import DatabaseAlreadyControlledError, DatabaseNotControlledError

        self.args = opts.args
        self.options = opts

        if len(self.args) < 2 or self.args[0] == 'help':
            self.args = ['help']
            return main(self.args)

        self._setup_logging()
        name = pkg_resources.safe_name(self.args.pop(0))
        sys.argv[0] = sys.argv[0] + ' migrate'

        if self.args[0] in ('create', 'script'):
            self._perform_appless_action(name)
            return

        # get sqlalchemy.url config in app:mains
        conf = ConfigParser()
        conf.read(opts.ini)

        try:
            sect = 'app:main'
            option = 'sqlalchemy.url'
            self.dburi = conf.get(sect, option, vars={'here':os.getcwd()})
        except:
            print("Unable to read config file or missing sqlalchemy.url in app:main section")
            return

        pluggables_to_migrate = []
        if name == 'all':
            pluggables_to_migrate.extend(self._detect_loaded_pluggables())
        else:
            pluggables_to_migrate.append(name)

        print('Migrating', ', '.join(pluggables_to_migrate))
        for pluggable in pluggables_to_migrate:
            try:
                self._perform_migration(pluggable)
            except DatabaseAlreadyControlledError:
                print('Pluggable already under version control...')
            except DatabaseNotControlledError:
                print('Your application is not under version control for this pluggable')
                print('Please run the version_control command before performing any other action.')