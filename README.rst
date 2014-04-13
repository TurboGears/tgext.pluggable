About Pluggable Apps
-------------------------

tgext.pluggable permits to plug extensions and applications inside a TG projects
much like the Django Apps.

Installing
-------------------------------

tgext.pluggable can be installed both from pypi or from bitbucket::

    pip install tgext.pluggable

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

If you want to mount the pluggable application in a subcontroller
you can used a dotted **appid**, like ``subcontroller.appid``.
Note that ``subcontroller`` must exist in RootController.


Other options include:

    - plug_helpers (True/False) -> Enable helpers injection
    - plug_models (True/False) -> Enable models plugging
    - plug_controller (True/False) -> Mount pluggable app root controller
    - plug_bootstrap (True/False) -> Enable websetup.bootstrap plugging
    - plug_statics (True/False) -> Enable plugged app statics
    - rename_tables (True/False) -> Rename pluggable tables by prepending appid.

Relations with Plugged Apps Models
--------------------------------------

There are cases when you might need to create a relationship or a foreign key
with a model which is defined by a pluggable application. As pluggable application
models are loaded after loading your application they are not available at the
time your app models are imported.

``tgext.pluggable`` provides some utilities to make easier to create relations
with models defined by pluggable applications.

The first step you might want to take is setting the ``global_models=True``
parameter to the ``plug`` call, this will make all the models declared by the
pluggable application available to you::

    plug(base_config, 'package_name', global_models=True)

After the specified pluggable application is plugged, the models will be available
inside your code through the ``tgext.pluggable.app_model`` object.

Then you can create foreign keys to the desired model using the
``tgext.pluggable.LazyForeignKey`` class and declare relations using the lazy
version of ``sqlalchemy.orm.relation``::

    from tgext.pluggable import app_model, LazyForeignKey

    class AdditionalInfo(DeclarativeBase):
        __tablename__ = 'sample_model'

        uid = Column(Integer, primary_key=True)
        data = Column(Unicode(255), nullable=False)

        plugged_model_id = Column(Integer, LazyForeignKey(lambda:app_model.PluggedModel.uid))
        plugged_model = relation(lambda: app_model.PluggedModel)


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

    from tgext.pluggable import load_template_patches

    load_template_patches(base_config)

Supposing your project is inside a Python distribution named **myapp** this will
load the ``template_patches.xml`` file from the root of the distribution and will
apply all the specified patches.

To load template patches from a python module (or pluggable) use::

    load_template_patches(base_config, 'plugname')

You can use previous expression even to load patches from your own application
in case the distribution automatic detection failed.

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

    $ gearbox quickstart-pluggable plugtest
    Enter package name [plugtest]:
    ...

The quickstarted application will provide an example on how to use
models, helpers, bootstrap, controllers and statics.

In the previous example the pluggable application can be enabled
inside any TurboGears using::

    plug(base_config, 'plugtest')

After enabling the *plugtest* application you should run
*gearbox setup-app* inside your TurboGears project
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

Changing Static Files Behavior
+++++++++++++++++++++++++++++++++++

By default every pluggable application serves all the static files available inside
its public directory as they are. This is performed by a WSGI application which is
in charge of serving the static files. Since version 0.2.1 it is now possible to
replace this application or apply any WSGI middleware to it through the
``static_middlewares`` option.

For example you can enable SCSS inside your pluggable application by
defining a ``plugme`` function like::

    from tgext.scss import SCSSMiddleware

    def plugme(app_config, options):
        return dict(appid='plugtest', global_helpers=False, static_middlewares=[SCSSMiddleware])
  
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

Internationalization
-------------------------------------

tgext.pluggable provides some utilities for to manage text translations inside
pluggables. When ``tg.i18n.ugettext`` or ``tg.i18n.lazy_ugettext`` are used
they will lookup for translations inside the Application and when not available
will fallback to the translations provided by the pluggable itself.
 
Messages extration and catalog creation/update for the pluggable work as in TurboGears 
using Babel. 
Just run inside the pluggable application the ``python setup.py extract_messages``
, ``python setup.py init_catalog -l LANG`` and ``python setup.py compile_catalog``
commands to create a catalog for ``LANG``.

Just distribute the catalogs with your pluggable application to make them
available and translated in applications that use it.

Managing Migrations
-------------------------------------

It is possible to initialize a migrations repository for a pluggable application.
This makes possible to evolve the database at later times for each pluggable application using
the `alembic <http://alembic.readthedocs.org/en/latest/tutorial.html#create-a-migration-script>`_ migration
library for SQLAlchemy.

Create Migration Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To be able to manage migrations the pluggable has to be initialized with a migration repository
to perform so, the author of the pluggable application has to run::

    $ gearbox migrate-pluggable plugtest init

Then to create migration scripts run::

    $ gearbox migrate-pluggable plugtest create 'Add column for user_name'

A file named like `2c8c79324a5e_Add_column_for_user_name.py` will be available inside the `migration/versions` directory
of the pluggable application.
*Remember to add this directory to your distribution package to make it available to users of your pluggable application*

Using Migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the pluggable application your are using supports migrations it is possible to apply them
using the `upgrade` and `downgrade` commands.

It is possible to run `upgrade` to move forward::

    $ gearbox migrate-pluggable plugtest upgrade
    22:11:28,029 INFO  [alembic.migration] Running upgrade None -> 3ca22a16fdcc

Or `downgrade` to revert a migration::

    $ gearbox migrate-pluggable plugtest downgrade
    22:15:24,004 INFO  [alembic.migration] Running downgrade 3ca22a16fdcc -> None

The versioning commands support being called on all the pluggables enabled inside your application
by specifying `all` as the pluggable name. This will load your application to detect the plugged
apps and will run the specified command for each one of them::

    $ gearbox migrate-pluggable all db_version
    22:15:54,104 INFO  [tgext.pluggable] Plugging plug1
    22:15:54,105 INFO  [tgext.pluggable] Plugging plug2
    22:15:54,106 INFO  [tgext.pluggable] Plugging plug3
    Migrating plug1, plug3, plug2
    
    plug1 Migrations
        Repository '/tmp/PLUGS/plug1/migration'
        Configuration File 'development.ini'
        Versioning Table 'plug1_migrate'
    22:15:54,249 INFO  [alembic.migration] Context impl SQLiteImpl.
    22:15:54,249 INFO  [alembic.migration] Will assume transactional DDL.
    Current revision for sqlite:////tmp/provaapp/devdata.db: 4edef05cc346 -> 1ae930148d69 (head), fourth migration
    
    plug3 Migrations
        Repository '/tmp/PLUGS/plug3/migration'
        Configuration File 'development.ini'
        Versioning Table 'plug3_migrate'
    22:15:54,253 INFO  [alembic.migration] Context impl SQLiteImpl.
    22:15:54,254 INFO  [alembic.migration] Will assume transactional DDL.
    Current revision for sqlite:////tmp/provaapp/devdata.db: 15819683bb72 -> 453f571f41e4 (head), test migration
    
    plug2 Migrations
        Repository '/tmp/PLUGS/plug2/migration'
        Configuration File 'development.ini'
        Versioning Table 'plug2_migrate'
    22:15:54,258 INFO  [alembic.migration] Context impl SQLiteImpl.
    22:15:54,259 INFO  [alembic.migration] Will assume transactional DDL.
    Current revision for sqlite:////tmp/provaapp/devdata.db: 154b4f69cbd1 -> 2c8c79324a5e (head), third migration
    
    
    
