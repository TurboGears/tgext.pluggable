from setuptools import setup, find_packages
import os

version = '0.0.2'

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
      url='http://bitbucket.org/_amol_/tgext.pluggable',
      license='MIT',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['tgext'],
      include_package_data=True,
      package_data = {'':['*.html', '*.js', '*.css', '*.png', '*.gif']},
      zip_safe=False,
      install_requires=[
        "TurboGears2 >= 2.1.4",
      ],
      entry_points="""
        [paste.global_paster_command]
        quickstart-pluggable = tgext.pluggable.commands.quickstart:QuickstartPluggableCommand
        [paste.paster_create_template]
        quickstart-pluggable-template=tgext.pluggable.commands.quickstart:QuickstartPluggableTemplate
      """,
      )
