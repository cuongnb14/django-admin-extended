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
    }

Usage
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
        
Screenshots
=======
- Change list page
.. image:: screenshots/change-list-page.png?raw=true

- Read only mode
.. image:: screenshots/view-mode.png?raw=true

- Edit mode
.. image:: screenshots/edit-mode.png?raw=true
