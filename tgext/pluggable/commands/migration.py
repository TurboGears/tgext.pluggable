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
import os, sys
import ConfigParser
from migrate.versioning.shell import main

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

    def command(self):
        sect = 'app:main'
        option = 'sqlalchemy.url'

        # get sqlalchemy.url config in app:mains
        conf = ConfigParser.ConfigParser()
        conf.read(self.options.ini)

        self.name = pkg_resources.safe_name(self.args.pop(0))
        try:
            self.repository = os.path.join(pkg_resources.get_distribution(self.name).location, 'migration')
        except pkg_resources.DistributionNotFound:
            print "pluggable %s not found" % self.name
            return

        if not os.path.exists(self.repository) and not self.args[0]=='create':
            print "pluggable not ready for migrations"
            return

        try:
            self.dburi = conf.get(sect, option, vars={'here':os.getcwd()})
        except:
            print "Unable to read config file or missing sqlalchemy.url in app:main section"
            return

        print "Migrations repository '%s',\ndatabase url '%s'\n"%(self.repository, self.dburi)
        if not self.args:
            self.args = ['help']
        sys.argv[0] = sys.argv[0] + ' migrate'
        tablename = self.name.replace('-', '_').replace('.', '_') + '_migrate'
        main(argv=self.args, url=self.dburi, repository=self.repository, name=self.name, version_table=tablename)