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
- Add link for foregin key in change list page
- And more utils functions


Install
=======

::

    pip install git+https://github.com/cuongnb14/django-admin-extended.git@v5.0#egg=django-admin-extended

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
- RAW_ID_FIELDS_AS_DEFAULT: use raw_id_fields (or autocomplete_fields if related model have search_fields) as default for related fields instead of select box



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

- **raw_id_fields_as_default** (boolean, default True) Use raw_id_fields (or autocomplete_fields if related model have search_fields) as default for ForeginKey instead of select box (optimize performance for large database)
- **delete_without_confirm** (boolean, default False) Ignore confirm page for delete action
- **tab_inline** (boolean, default from setting) Use tab for model inline (override value in setting)
- **super_admin_only_fields** (list, default []) Only show these fields if user login is superuser
- **ext_read_only_fields** (list, default []) Only show these fields in view mode. Default custom fields start with `display_` was mark as read only so you don't need add these fields to ext_read_only_fields
- **ext_write_only_fields** (list, default []) Only show these fields in edit mode
- **enable_foreign_link** (boolean, default True) Add link for foregin key in change list page


Advand
=======
Add custom object tools item in change list or change form
------

.. code:: python

    from admin_extended.decorators import object_tool
    from admin_extended.base import ExtendedAdminModel

    @admin.register(models.Customer)
    class CustomerAdmin(ExtendedAdminModel):
        change_form_object_tools = ['demo_change_form_action']
        change_list_object_tools = ['demo_change_list_action']

        @object_tool(icon='fas fa-edit', name='do_something', description='Do something', http_method='post', post_param_title='Name')
        def demo_change_form_action(self, request, object_id):
            customer = models.Customer.objects.get(pk=object_id)
            context = {
                **admin.site.each_context(request),
                'title': f'Update customer {customer.name}',
            }
            if request.method == 'POST':
                form = CustomForm(request.POST)
                messages.success(request, request.POST.get('data'))
                if form.is_valid():
                    print(form.cleaned_data)
                    return redirect(reverse('admin:shop_customer_change', args=[object_id]))
            context["form"] = CustomForm()
            return render(request, 'admin/custom/custom_form.html', context)
        
        @object_tool(icon='fas fa-edit', name='demo_change_list_action', description='Do something')
        def demo_change_list_action(self, request):
            context = {
                **admin.site.each_context(request),
                'title': f'Import customer',
            }
            if request.method == 'POST':
                form = CustomForm(request.POST)
                if form.is_valid():
                    print(form.cleaned_data)
                    return redirect(reverse('admin:shop_customer_changelist'))
            context["form"] = CustomForm()
            return render(request, 'admin/custom/custom_form.html', context)

**Result**

- Change list object tool
.. image:: screenshots/demo-change-list-object-tools.png?raw=true

- Change form object tool
.. image:: screenshots/demo-change-form-object-tools.png?raw=true
.. image:: screenshots/demo-custom-object-tools.png?raw=true


**object_tool(function=None, *, icon=None, name=None, description=None, http_method='get', post_param_title=None)**

- icon: icon of button
- name: name of object tool (must unique)
- description: label of button
- http_method: Only affect in change form page. with http_method is post, you can pass one param when submit object tool.
- post_param_title: Only affect when http_method is post. Title of param you want to pass.

Add bookmark
------
- Go to page you want add to bookmark
- Click bookmark button add bottom right
- Choose name of bookmark
- You also can manage book mark (add, delete, change order, ...) in bookmark model

.. image:: screenshots/demo-bookmark.png?raw=true

Automatically Register All Models In Django Admin
----
Add this code at **end of admin.py file** of **lastest install app (INSTALLED_APPS setting)**

.. code:: python
    
    from admin_extended.utils import auto_register_model_admin

    auto_register_model_admin()

**auto_register_model_admin(default_model_admin_class=DefaultModelAdmin, ignore_models=[]):**
This function will automatic register admin for all unregistered model 

- default_model_admin_class: DefaultModelAdmin will list all fields (exclude TextField) of model in change list page, you can custom your model admin and pass to this param
- ignore_models: list model you don't want auto register. specify by <app_label>.<model_name>. Eg: 'users.user'


Screenshots
=======
- Change list page
.. image:: screenshots/change-list-page.png?raw=true

- Read only mode
.. image:: screenshots/view-mode.png?raw=true

- Edit mode
.. image:: screenshots/edit-mode.png?raw=true
