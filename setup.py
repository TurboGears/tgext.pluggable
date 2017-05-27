from setuptools import setup, find_packages
import os

version = '0.7.0'

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
except IOError:
    README = ''

setup(name='tgext.pluggable',
      version=version,
      description="Plug applications and extensions in a TurboGears2 project",
      long_description=README,
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Environment :: Web Environment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: TurboGears"
        ],
      keywords='turbogears2.extension',
      author='Alessandro Molina',
      author_email='alessandro.molina@axant.it',
      url='https://github.com/TurboGears/tgext.pluggable',
      license='MIT',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['tgext'],
      include_package_data=True,
      package_data = {'':['*.html', '*.js', '*.css', '*.png', '*.gif']},
      zip_safe=False,
      install_requires=[
        "TurboGears2 >= 2.2.0",
        "gearbox"
      ],
      entry_points={
          'gearbox.commands': [
              'quickstart-pluggable = tgext.pluggable.commands.quickstart:QuickstartPluggableCommand',
              'sqla-migrate-pluggable = tgext.pluggable.commands.migration:MigrateCommand',
              'migrate-pluggable = tgext.pluggable.commands.alembic_migration:MigrateCommand',
              'plug = tgext.pluggable.commands.plug:PlugApplicationCommand'
          ]
      })
