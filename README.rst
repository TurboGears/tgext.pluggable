About Pluggable Apps
-------------------------

tgext.pluggable permits to plug extensions and applications inside a TG projects
much like the Django Apps.

**tgext.pluggable** IS STILL EXPERIMENTAL AND MIGHT CHANGE IN THE FUTURE

Installing
-------------------------------

tgext.pluggable can be installed both from pypi or from bitbucket::

    easy_install tgext.pluggable

should just work for most of the users

Plugging Apps
----------------------------

In your application *config/app_cfg.py* import **plug**::

    from tgext.pluggable import plug

Then at the *end of the file* call plug for each pluggable
application you want to enable (package_name must be
already installed in your python environment)::

    plug(base_config, 'package_name')

The plug function accepts various optional arguments, for
example if the plugged application exposes a controller
you can mount it in a different place specifying a different
**appid**::

    plug(base_config, 'package_name', 'new_app_id')

Other options include:

    - plug_helpers (True/False) -> Enable helpers injection
    - plug_models (True/False) -> Enable models plugging
    - plug_controller (True/False) -> Mount pluggable app root controller
    - plug_bootstrap (True/False) -> Enable websetup.bootstrap plugging
    - plug_statics (True/False) -> Enable plugged app statics
    - rename_tables (True/False) -> Rename pluggable tables by prepending appid.

Creating Pluggable Apps
----------------------------

tgext.pluggable provides a **quickstart-pluggable** command
to create a new pluggable application::

    $ paster quickstart-pluggable plugtest
    Enter package name [plugtest]:
    ...

The quickstarted application will provide an example on how to use
models, helpers, bootstrap, controllers and statics.

In the previous example the pluggable application can be enabled
inside any TurboGears using::

    plug(base_config, 'plugtest')

After enabling the *plugtest* application you should run
*paster setup-app development.ini* inside your TurboGears project
to create the sample model. Then you can access the sample
application page though *http://localhost:8080/plugtest*
