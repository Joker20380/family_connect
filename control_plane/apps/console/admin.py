from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group
from . import models, workflow

admin.site.site_header = 'Family Connect · Панель управления'
admin.site.site_title = 'Панель демо Beta-0'
admin.site.index_title = 'Операционные метаданные · не источник решений о доступе'
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
    list_display = ('id', 'device', 'purpose', 'amount_minor', 'currency', 'confirmed_at')
    list_filter = ('purpose', 'currency', 'confirmed_at')
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


@admin.register(models.InventorySnapshot)
class SnapshotAdmin(ReadOnlyAdmin):
    list_display = ('source', 'scope', 'observed_at', 'imported_at', 'registry_status')
    list_filter = ('scope', 'source', 'registry_status')


@admin.register(models.InventoryDevice)
class InventoryAdmin(ReadOnlyAdmin):
    list_display = ('pseudonym', 'snapshot', 'version_code', 'activated', 'revoked')
    search_fields = ('pseudonym',)
    list_filter = ('activated', 'revoked', 'version_code')


@admin.register(models.TechnicalSample)
class SampleAdmin(ReadOnlyAdmin):
    list_display = ('scope', 'source', 'device', 'metric', 'value', 'observed_at')
    list_filter = ('scope', 'source', 'metric')
    search_fields = ('device__label',)


admin.site.register(models.ServerObservation, ReadOnlyAdmin)
admin.site.register(models.OperationSwitch, ReadOnlyAdmin)


class RussianPermissionLabels:
    def formfield_for_manytomany(self, database_field, request, **kwargs):
        field = super().formfield_for_manytomany(database_field, request, **kwargs)
        if database_field.name in ('permissions', 'user_permissions'):
            def permission_label(permission):
                action = permission.codename.split('_', 1)[0]
                verb = {'add': 'Добавление', 'change': 'Изменение', 'delete': 'Удаление', 'view': 'Просмотр'}.get(action)
                return f'{permission.content_type.name} · {verb}' if verb else permission.name
            field.label_from_instance = permission_label
        return field


class RussianUserAdmin(RussianPermissionLabels, UserAdmin):
    pass


class RussianGroupAdmin(RussianPermissionLabels, GroupAdmin):
    pass


admin.site.unregister(get_user_model())
admin.site.unregister(Group)
admin.site.register(get_user_model(), RussianUserAdmin)
admin.site.register(Group, RussianGroupAdmin)
