from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from control.friends import paid_beta
from apps.console import backend, workflow
from apps.console.models import ReleaseMetadata


class Command(BaseCommand):
    help = 'Initialize isolated synthetic identities and readonly projections; never real users or paid enrollment'

    @transaction.atomic
    def handle(self, *args, **options):
        backend.seed_fixture()
        for member in backend.members():
            workflow.refresh(member['device'])
        permissions = Permission.objects.filter(content_type__app_label='console')
        viewer, _ = Group.objects.get_or_create(name='Control-plane viewers')
        viewer.permissions.set(permissions.filter(codename__startswith='view_'))
        operator, _ = Group.objects.get_or_create(name='Control-plane operators')
        actions = {'add_paymentrecord', 'confirm_payment', 'add_operationrequest', 'preview_operation', 'execute_operation',
                   'add_cohortmetadata', 'change_cohortmetadata', 'add_incident', 'change_incident'}
        operator.permissions.set([permission for permission in permissions if permission.codename.startswith('view_') or permission.codename in actions])
        values = dict(version_code=106, package_id='com.familyconnect.app.friends', size=56093664,
            sha256=paid_beta.APK_SHA256, signer_sha256='67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a',
            channel='private verified handoff only')
        release, _ = ReleaseMetadata.objects.get_or_create(version_name=paid_beta.VERSION, defaults=values)
        if any(getattr(release, name) != value for name, value in values.items()):
            raise CommandError('Accepted release metadata differs; operator review required')
        self.stdout.write('Synthetic fixture ready: 12 identities (11 exact106 observations, one older-version negative fixture). No new paid enrollment. No user passwords created.')
