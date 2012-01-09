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

Partials
--------------------------

tgext.pluggables provides a bunch of utilities to work with partials.
Partials in tgext.pluggable can be declared as a function or TGController
subclass method that has an *@expose* decorator. Those partials can lately
be rendered with::

    ${h.call_partial('module:function_name', arg1='Something')}

In the case of a class method::

    ${h.call_partial('module.Class:method', arg1='Something')}

The quickstarted pluggable application provides an example partial::

    from tg import expose

    @expose('plugappname.templates.little_partial')
    def something(name):
        return dict(name=name)

which can be rendered using::

    ${h.call_partial('plugappname.partials:something', name='Partial')}

Replacing Templates
--------------------------

tgext.pluggable provides a function to replace templates.
This is useful when you want to override the template that an application
you plugged in is exposing. To override call **replace_template** inside
your application config::

    from tgext.pluggable replace_template

    replace_template(base_config, 'myapp.templates.about', 'myapp.templates.index')

**replace_template** will work even with tgext.pluggable partials, but
won't work with templates rendered directly calling the **render** method.

Calls to replace_template must be performed before the application has started.

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

