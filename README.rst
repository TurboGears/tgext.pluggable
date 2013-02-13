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

    from tgext.pluggable import replace_template

    replace_template(base_config, 'myapp.templates.about', 'myapp.templates.index')

**replace_template** will work even with tgext.pluggable partials, but
won't work with templates rendered directly calling the **render** method.

Calls to replace_template must be performed before the application has started.

Patching Templates
----------------------------

tgext.pluggable provides a function to patch templates, the result
of a template rendering will be passed through a list of operations which will
make possible to alter the rendering result.

This behavior is much inspired by **Deliverance** http://pythonhosted.org/Deliverance
meant for much simpler use cases. The most common usage is for small changes to templates
of plugged applications. For advanced manipulations using `replace_template` is suggested
as it's both faster and easier to maintain.

Template patching is enabled by using the `load_template_patches` function::

    from tgext.pluggable import replace_template

    load_template_patches(base_config)

To load template patches from a python module (or pluggable) use::

    load_template_patches(base_config, 'plugname')

Template patching format is an xml file in the form of::

    <patches>
      <patch template="tgext.crud.templates.get_all">
        <content selector="#crud_content > h1" template="myapp.templates.replacements.crud_title" />
        <append  selector="#crud_content > h1" template="myapp.templates.replacements.crud_subtitle" />
        <prepend selector="#crud_content > h1" template="myapp.templates.replacements.crud_superscript" />
        <replace selector="#crud_btn_new > .add_link" template="" />
      </patch>
    </patches>

Each action listed inside the patch will be performed whenever the specified template
is rendered, the template associated to the action will be used as the content of the templacement
and the same data available to the patched template will be available to the action template too.
Available actions are:

    * `content` - replaces the content of tags identified by the selector

    * `append` - appends after the tags identified by the selector

    * `prepend` - prepends before the tags identified by the selector

    * `replace` - replaces the tags identified bt the selector.

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

Managing Migrations
-------------------------------------

It is possible to initialize a migrations repository for a pluggable application.
This makes possible to evolve the database at later times for each pluggable application.

Create Migration Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To be able to manage migrations the pluggable has to be initialized with a migration repository
to perform so, the author of the pluggable application has to run::

    $ paster migrate-pluggable plugtest create

Then to create migration scripts run::

    $ paster migrate-pluggable plugtest script 'Add column for user_name'

A file named `001_Add_column_for_user_name.py` will be available inside the `migration/versions` directory
of the pluggable application.
*Remember to add this directory to your distribution package to make it available to users of your pluggable application*

Using Migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the pluggable application your are using supports migrations it is possible to apply them
using the `upgrade` and `downgrade` commands. If is the first time your application runs a migration
for such a pluggable it is necessary to run the `version_control` command before any other::

    $ paster migrate-pluggable plugtest version_control

Then it is possible to run `upgrade` to move forward::

    $ paster migrate-pluggable plugtest upgrade
    0 -> 1...
    done

Or `downgrade` to revert a migration::

    $ paster migrate-pluggable plugtest upgrade 0
    1 -> 0...
    done

The versioning commands support being called on all the pluggables enabled inside your application
by specifying `all` as the pluggable name. This will load your application to detect the plugged
apps and will run the specified command for each one of them::

    $ paster migrate-pluggable all db_version
    Plugging plug1
    Plugging plug2
    Plugging plug3
    Migrating plug1, plug3, plug2

    plug1 Migrations
        Repository '/tmp/migrt/plug1/migration'
        Database 'sqlite:////tmp/migrt/coreapp/devdata.db'
        Versioning Table 'plug1_migrate'
    0

    plug3 Migrations
        Repository '/tmp/migrt/plug3/migration'
        Database 'sqlite:////tmp/migrt/coreapp/devdata.db'
        Versioning Table 'plug3_migrate'
    0

    plug2 Migrations
        Repository '/tmp/migrt/plug2/migration'
        Database 'sqlite:////tmp/migrt/coreapp/devdata.db'
        Versioning Table 'plug2_migrate'
    0


