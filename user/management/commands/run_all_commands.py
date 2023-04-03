import time
from subprocess import Popen
from sys import stderr, stdin, stdout

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run all commands"
    commands = [
        # 'python manage.py create_menus',
        # Run in order for prov and district
        "python manage.py create_privilege",
        "python manage.py create_menus",
    ]

    def handle(self, *args, **options):
        proc_list = []

        for command in self.commands:
            print("$ " + command)
            proc = Popen(command, shell=True, stdin=stdin, stdout=stdout, stderr=stderr)
            proc_list.append(proc)

            time.sleep(5)

        # try:
        #     while True:
        # except KeyboardInterrupt:
        #     for proc in proc_list:
        #         os.kill(proc.pid, signal.SIGKILL)

        print(".......All Commands Successful .......")
