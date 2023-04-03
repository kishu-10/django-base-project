from user.models import Privilege
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Privileges Setup"

    def handle(self, *args, **options):

        privileges = [
            {
                "name": "Create",
                "code": "can_create",
                "is_active":True
            },
            {
                "name": "Read",
                "code": "can_read",
                "is_active":True,
            },
            {
                "name": "Update",
                "code": "can_update",
                "is_active":True,
            },

            {
                "name": "Delete",
                "code": "can_delete",
                "is_active":True,
            },
            {
                "name": "Approve",
                "code": "can_approve",
                "is_active":True,
            },
            {
                "name": "Configure",
                "code": "can_configure",
                "is_active":True,
            },
            {
                "name": "Transfer",
                "code":"can_transfer",
                "is_active":True,
            },
            
            
 
        ]
        for privilege in privileges:
            Privilege.objects.update_or_create(code=privilege['code'],defaults ={
                'name': privilege.get('name'),
                'is_active':privilege.get('is_active')
            })

        print("Privilege command executed successfully.")
