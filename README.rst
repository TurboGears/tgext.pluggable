About Pluggable Apps
-------------------------

tgext.pluggable permits to plug extensions and applications inside a TG projects
much like the Django Apps.

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

The plugme Entry Point
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pluggable applications are required to implement a **plugme(app_config, options)** entry
point which will be called when plugging the application.

The plugme action is called before TurboGears configuration has been loaded so that
it is possible to register more pluggables inside the plugme hook. This way a pluggable
can plug any dependency it requires just by calling tgext.pluggable.plug inside its own
*plugme* function.

Any options passed to the plug call will be available inside the options dictionary,
other parts of the pluggable applications like controllers, models and so on will be
imported after the call to plugme so that plugme can set any configuration options that
will drive the behavior of the other parts.

Keep in mind that as plugme is called before loading the TurboGears configuration if you
need to perform something based on any configuration file option you must register a *setup*
from the plugme call and perform them there.

Accessing Application Models from Pluggable Apps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When creating a pluggable application you might often need to
access to some models that have been declared inside the
target application where the pluggable app will be mounted.

The most common use case for this is referencing the User, Group and Permission
models. To do this tgext.pluggable provides an **app_model** object which
wraps the application model and is initialized before loading the pluggable app.

This makes possible to access target application models referencing
them as **app_model.User** or **app_model.Group** and so on.
While you can guess that the primary key for those models is known
(for the app_model.User object for example you might consider referencing
to it as app_model.User.user_id) it is best practice to call the **primary_key**
function provided by tgext.pluggable to get a reference to its column.

This way it is possibile to declare relations to models which are not
provided by your pluggable app::

    from tgext.pluggable import app_model, primary_key

    user_id = Column(Integer, ForeignKey(primary_key(app_model.User)))
    user = relation(app_model.User)

Pluggable Relative Urls
----------------------------------

It is possible to generate an url relative to a pluggable mount point
using the **plug_url(pluggable, path, params=None, lazy=False)** this
function is also exposed inside the application helpers when a pluggable
is used. For example to generate an url relative to the *plugtest* pluggable
it is possible to call plug_url::

    plug_url('plugtest', '/')

To perform redirects inside a pluggable app the **plug_redirect(pluggable, path, params=None)**
function is provided. This function exposes the same interface as *plug_url* but
performs a redirect much like tg.redirect.