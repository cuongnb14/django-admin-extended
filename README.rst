Django Admin Extended
===================

Enhance UI/UX of django admin

**Features:**

- Custom order menu item
- Restyle sidebar menu UI, collapse menu
- Integrate icon fontawesome free v5: https://fontawesome.com/v5.15/icons?d=gallery&p=2&m=free
- Custom icon for menu app
- Restyle align for form row in change page
- Collapse filter box
- Admin inlines tabbable
- Read only mode
- Bookmark menu
- Ignore confirm delete page option
- And more utils functions

Install
=======

::

    pip install git+https://github.com/cuongnb14/django-admin-extended.git@master#egg=django-admin-extended

Setting
=======

.. code:: python

    # Install app, install before django.contrib.admin
    INSTALLED_APPS = [
        'fontawesomefree',
        'admin_extended',
        'django.contrib.admin',
        ...
    ]

    ADMIN_EXTENDED = {
        'MENU_APP_ORDER': ['user', 'auth'],
        'MENU_MODEL_ORDER': ['User', 'Group'],
        'APP_ICON': {
            'user': 'fas fa-user',
            'auth': 'fas fa-users',
        },
        'MODEL_ADMIN_TABBED_INLINE': True,
        'RAW_ID_FIELDS_AS_DEFAULT': False,
    }
    
- MENU_APP_ORDER: change order of app at left sidebar
- MENU_MODEL_ORDER: change order of model at left sidebar
- APP_ICON: custom icon of menu app use fontawesome v5 (https://fontawesome.com/v5.15/icons?d=gallery&p=2&m=free)
- MODEL_ADMIN_TABBED_INLINE: use tab for model inline. Default is True
- RAW_ID_FIELDS_AS_DEFAULT: use raw_id_fields as default for ForeginKey instead of select box



Basic Usage
=======

.. code:: python

    from django.apps import apps
    from django.contrib import admin
    from admin_extended.base import ExtendedAdminModel
    from . import models



    class PostCommentInline(admin.TabularInline):
        model = models.PostComment
        extra = 0

    class PostTagInline(admin.TabularInline):
        model = models.PostTag
        extra = 0

    @admin.register(models.Post)
    class PostAdmin(ExtendedAdminModel):
        list_display = ('id', 'title', 'post_at')
        search_fields = ('title',)
        search_help_text = 'Search by title'
        list_filter = ('status',)
        inlines = [
            PostCommentInline,
            PostTagInline
        ]

**ExtendedAdminModel options**

- **raw_id_fields_as_default** (boolean, default True) Use raw_id_fields as default for ForeginKey instead of select box (optimize performance for large database)
- **delete_without_confirm** (boolean, default False) Ignore confirm page for delete action
- **tab_inline** (boolean, default from setting) Use tab for model inline (override value in setting)
- **super_admin_only_fields** (list, default []) Only show these fields if user login is superuser
- **ext_read_only_fields** (list, default []) Only show these fields in view mode. Default custom fields start with `display_` was mark as read only so you don't need add these fields to ext_read_only_fields
- **ext_write_only_fields** (list, default []) Only show these fields in edit mode


Advand
=======
Add custom object tools item in change form
------

Suppose you have a custom admin page with url name 'admin:do_some_thing', you can add link of this page to object tools


.. code:: python

    class CustomerAdmin(ExtendedAdminModel):
        def get_change_form_object_tools(self, request, object_id):
            return [{
                'icon': 'fas fa-edit',
                'url': reverse('admin:do_some_thing', args=[object_id]),
                'title': 'Custom action',
            }]
            return []

Result

.. image:: screenshots/demo-custom-object-tools.png?raw=true

Add bookmark
------
- Go to page you want add to bookmark
- Click bookmark button add bottom right
- Choose name of bookmark
- You also can manage book mark (add, delete, change order, ...) in bookmark model

.. image:: screenshots/demo-bookmark.png?raw=true




Screenshots
=======
- Change list page
.. image:: screenshots/change-list-page.png?raw=true

- Read only mode
.. image:: screenshots/view-mode.png?raw=true

- Edit mode
.. image:: screenshots/edit-mode.png?raw=true
