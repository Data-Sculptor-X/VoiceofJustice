# import_laws.py

import json
from django.core.management.base import BaseCommand
from core.models import Law

class Command(BaseCommand):
    help = 'Imports laws from a JSON file into the database'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')

    def handle(self, *args, **options):
        json_file = options['json_file']

        with open(json_file, 'r') as file:
            data = json.load(file)

        laws_to_create = []
        for item in data:
            law = Law(
                act=item.get('Act ID', ''),
                actName=item.get('Act Title', ''),
                description=item.get('Act Definition', ''),
                data=item.get('data', item)
            )
            laws_to_create.append(law)

        Law.objects.bulk_create(laws_to_create)

        self.stdout.write(self.style.SUCCESS('Successfully imported laws from JSON file'))
