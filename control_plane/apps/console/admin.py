from django.contrib import admin
from . import models, workflow

admin.site.site_header = 'Family Connect · Control Plane 0'
admin.site.site_title = 'Synthetic Beta-0 console'
admin.site.index_title = 'Operational metadata · never entitlement authority'
admin.site.index_template = 'admin/console_index.html'


class ReadOnlyAdmin(admin.ModelAdmin):
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.DeviceProjection)
class DeviceAdmin(ReadOnlyAdmin):
    list_display = ('label', 'device', 'observed_at')
    search_fields = ('device', 'label')


@admin.register(models.PaymentRecord)
class PaymentAdmin(ReadOnlyAdmin):
    list_display = ('id', 'device', 'amount_minor', 'currency', 'confirmed_at')
    list_filter = ('currency', 'confirmed_at')
    search_fields = ('device__device', 'reference_hash')


@admin.register(models.OperationRequest)
class OperationAdmin(ReadOnlyAdmin):
    list_display = ('id', 'device', 'action', 'status', 'created_at')
    list_filter = ('action', 'status')
    search_fields = ('device__device', 'device__label')


@admin.register(models.AuditRecord)
class AuditAdmin(ReadOnlyAdmin):
    list_display = ('occurred_at', 'actor', 'action', 'target')
    list_filter = ('action',)
    search_fields = ('target',)


@admin.register(models.ReleaseMetadata)
class ReleaseAdmin(ReadOnlyAdmin):
    list_display = ('version_name', 'version_code', 'channel', 'sha256')


class MetadataAdmin(admin.ModelAdmin):
    actions = None
    readonly_fields = ('updated_at',)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        workflow.audit(request.user, obj._meta.model_name + ('.update' if change else '.create'), obj.pk)


@admin.register(models.CohortMetadata)
class CohortAdmin(MetadataAdmin):
    list_display = ('device', 'opted_in', 'handoff_verified', 'owner', 'updated_at')
    list_filter = ('opted_in', 'handoff_verified')
    search_fields = ('device__label', 'device__device')


@admin.register(models.Incident)
class IncidentAdmin(MetadataAdmin):
    list_display = ('device', 'category', 'severity', 'status', 'owner', 'updated_at')
    list_filter = ('category', 'severity', 'status')
    search_fields = ('device__label', 'device__device')
