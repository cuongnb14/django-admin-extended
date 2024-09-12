from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .. import models


@admin.register(models.Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'is_active', 'order')
    list_filter = ('is_active',)
    list_editable = ('is_active', 'order')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'add-bookmark', self.admin_site.admin_view(self.add_bookmark_view), name='admin_extended_add_bookmark'
            ),
        ]
        return custom_urls + urls

    @method_decorator(csrf_exempt)
    def add_bookmark_view(self, request):
        if request.method == 'POST':
            name = request.POST.get('name')
            url = request.POST.get('url')
            models.Bookmark.objects.create(
                name=name,
                url=url,
            )
            return HttpResponse()
