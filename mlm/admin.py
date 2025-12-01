from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from .models import MLMNode

@admin.register(MLMNode)
class MLMNodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'parent', 'position', 'active', 'created_at')
    search_fields = ('user__username', 'user__email')
    change_list_template = "mlm/admin_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        model_label = f"{self.model._meta.app_label}_{self.model._meta.model_name}"
        custom_urls = [
            path('tree-visualization/', self.admin_site.admin_view(self.tree_visualization),
                 name=f'{model_label}_tree_visualization'),
        ]
        return custom_urls + urls

    def tree_visualization(self, request):
        # compute a sensible root node for admin visualization:
        root = MLMNode.objects.filter(parent__isnull=True).order_by('created_at').first()
        root_id = root.id if root else None

        context = dict(
            self.admin_site.each_context(request),
            root_id=root_id,
        )
        return TemplateResponse(request, "mlm/tree_admin.html", context)
