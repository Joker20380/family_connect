from django.contrib import admin

from apps.console.admin import ReadOnlyAdmin
from .models import LogicalGateway, GatewayInstance, GatewayArtifact, EnrollmentToken, DeploymentOperation, InstanceHealthCheck


@admin.register(GatewayInstance)
class InstanceAdmin(ReadOnlyAdmin):
    list_display = ('instance_id','logical_gateway','provider','region','ipv4','desired_bundle','actual_bundle','state','health_state')
    list_filter = ('state','health_state','provider')
    search_fields = ('instance_id','logical_gateway__id')


@admin.register(GatewayArtifact)
class ArtifactAdmin(ReadOnlyAdmin):
    list_display = ('bundle_id','source_commit','manifest_sha256','archive_sha256','signature_verified','supported_os','roles')


@admin.register(DeploymentOperation)
class OperationAdmin(ReadOnlyAdmin):
    list_display = ('operation_id','instance','action','state','first_failure','started_at','completed_at')


@admin.register(InstanceHealthCheck)
class HealthAdmin(ReadOnlyAdmin):
    list_display = ('instance','scope','observed_at','cpu','ram','disk','active_sessions','restart_count','certificate_expiry','directory_expiry')


admin.site.register(LogicalGateway,ReadOnlyAdmin)
admin.site.register(EnrollmentToken,ReadOnlyAdmin)
