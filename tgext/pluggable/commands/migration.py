"""
tgext.pluggable migration

paster migrate-pluggable command integrate sqlalchemy-migrate into tgext.pluggable.

To start a migration, run command::

    $ paster migrate-pluggable create

And migrate-pluggable command will create a 'migration' directory for you.
With migrate-pluggable command you don't need use 'manage.py' in 'migration' directory anymore.

Then you could bind the database with migration with command::

    $ paster migrate-pluggable version_control

Usage:

.. parsed-literal::

   paster migrate-pluggable PLUGNAME help
   paster migrate-pluggable PLUGNAME create
   paster migrate-pluggable PLUGNAME vc|version_control
   paster migrate-pluggable PLUGNAME dbv|db_version
   paster migrate-pluggable PLUGNAME v|version
   paster migrate-pluggable PLUGNAME manage [script.py]
   paster migrate-pluggable PLUGNAME test [script.py]
   paster migrate-pluggable PLUGNAME ci|commit [script.py]
   paster migrate-pluggable PLUGNAME up|upgrade [--version]
   paster migrate-pluggable PLUGNAME downgrade [--version]

.. container:: paster-usage

  --version
      database's version number

check http://code.google.com/p/sqlalchemy-migrate/wiki/MigrateVersioning for detail.

"""

import pkg_resources
from paste.script import command
import os, sys, logging
import ConfigParser
from migrate.exceptions import DatabaseAlreadyControlledError, DatabaseNotControlledError
from migrate.versioning.shell import main
from paste.deploy import loadapp
from tgext.pluggable import plugged

class MigrateCommand(command.Command):
    """Create and apply SQLAlchemy migrations
Migrations will be managed inside the 'migration/versions' directory

Usage: paster migrate-pluggable PLUGNAME COMMAND ...
Use 'paster migrate-pluggable PLUGNAME help' to get list of commands and their usage

Create a new migration::

    $ paster migrate-pluggable PLUGNAME script 'Add New Things'

Apply migrations::

    $ paster migrate-pluggable PLUGNAME upgrade
"""

    version = pkg_resources.get_distribution('tgext.pluggable').version
    min_args_error = __doc__
    summary = __doc__.splitlines()[0]
    usage = '\n' + __doc__
    group_name = "TurboGears2"

    parser = command.Command.standard_parser(verbose=True)
    parser.add_option("-c", "--config",
        help='application config file to read (default: development.ini)',
        dest='ini', default="development.ini")

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
            print "%s - pluggable not found" % pluggable
            return None

    def _detect_loaded_pluggables(self):
        app = loadapp('config:%s' % self.options.ini, relative_to=os.getcwd())
        return plugged()

    def _perform_migration(self, pluggable):
        repository = self._pluggable_repository(pluggable)
        if repository is None or not os.path.exists(repository):
            print "%s - Pluggable does not support migrations" % pluggable
            return

        tablename = self._pluggable_tablename(pluggable)
        print '\n%s Migrations' % pluggable
        print "\tRepository '%s'" % repository
        print "\tDatabase '%s'" % self.dburi
        print "\tVersioning Table '%s'" % tablename

        #disable logging, this is due to sqlalchemy-migrate bug that
        #causes the disable_logging option to ignored
        args = self.args[:1] + ['-q'] + self.args[1:]

        main(argv=args, url=self.dburi, repository=repository, name=pluggable,
             version_table=tablename, disable_logging=True)

    def _perform_appless_action(self, pluggable):
        repository = self._pluggable_repository(pluggable)
        if repository is None:
            return

        tablename = self._pluggable_tablename(pluggable)
        print "\n%s Migrations" % pluggable
        print "\tRepository '%s'" % repository
        print "\tVersioning Table '%s'" % tablename

        #disable logging, this is due to sqlalchemy-migrate bug that
        #causes the disable_logging option to ignored
        args = self.args[:1] + ['-q'] + self.args[1:]

        main(argv=args, url=None, repository=repository, name=pluggable,
             version_table=tablename, disable_logging=True)

    def command(self):
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
        conf = ConfigParser.ConfigParser()
        conf.read(self.options.ini)

        try:
            sect = 'app:main'
            option = 'sqlalchemy.url'
            self.dburi = conf.get(sect, option, vars={'here':os.getcwd()})
        except:
            print "Unable to read config file or missing sqlalchemy.url in app:main section"
            return

        pluggables_to_migrate = []
        if name == 'all':
            pluggables_to_migrate.extend(self._detect_loaded_pluggables())
        else:
            pluggables_to_migrate.append(name)

        print 'Migrating', ', '.join(pluggables_to_migrate)
        for pluggable in pluggables_to_migrate:
            try:
                self._perform_migration(pluggable)
            except DatabaseAlreadyControlledError:
                print 'Pluggable already under version control...'
            except DatabaseNotControlledError:
                print 'Your application is not under version control for this pluggable'
                print 'Please run the version_control command before performing any other action.'