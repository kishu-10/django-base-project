from user.models import Menu, Privilege
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "menus setup"

    def handle(self, *args, **options):

        menus = []
        i = 0

        for menu in menus:
            i += 1
            if menu.get("parent", None):
                try:
                    parent_menu = Menu.objects.get(code=menu.get("parent"))
                except Exception:
                    parent_menu = None
            else:
                parent_menu = None
            menu, created = Menu.objects.update_or_create(
                code=menu["code"],
                defaults={
                    "parent": parent_menu,
                    "name": menu["name"],
                    "is_active": menu.get("is_active", True),
                    "order_id": menu.get("order_id", i),
                    "url": menu.get("url"),
                    "icon": menu.get("icon", ""),
                },
            )

            if menu.user_type == "1":
                menu.privilege.set(Privilege.objects.filter(is_active=True))

        print(".... User Menus Loaded Successfully...")
