Django Admin Reskin
===================
**Features:**

- Custom order menu item
- Restyle sidebar menu UI
- Integrate icon fontawesome free v5: https://fontawesome.com/v5.15/icons?d=gallery&p=2&m=free
- Restyle align for form row in change page
- Bookmark menu

Install
=======

::

    pip install git+https://github.com/cuongnb14/django-admin-reskin.git@master#egg=django-admin-reskin

Setting
=======

.. code:: python

    # Install app
    INSTALLED_APPS = [
        'fontawesomefree',
        'admin_reskin',
        'django.contrib.admin',
        ...
    ]

    # Menu app order
    RESKIN_MENU_APP_ORDER = [
        "user",
        "auth"
    ]

    # Menu model order
    RESKIN_MENU_MODEL_ORDER = [
        "User",
        "Group",
    ]

    RESKIN_APP_ICON = {
        'user': 'fas fa-user',
        'auth': 'fas fa-users',
    }

