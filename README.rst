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

    ADMIN_EXTENDED_SETTINGS = {
        'MENU_APP_ORDER': ['user', 'auth'],
        'MENU_MODEL_ORDER': ['User', 'Group'],
        'APP_ICON': {
            'user': 'fas fa-user',
            'auth': 'fas fa-users',
        },
        'MODEL_ADMIN_TABBED_INLINE': True,
    }

Screenshots
=======

.. image:: screenshots/change-list-page.png?raw=true

.. image:: screenshots/view-mode.png?raw=true

.. image:: screenshots/edit-mode.png?raw=true
