
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_date

from billing.services import generate_monthly_rent_records


class Command(BaseCommand):
    help = "Generate missing monthly rent records for active agreements."

    def add_arguments(self, parser):
        parser.add_argument(
            "--as-of",
            type=str,
            help="Generate records through this date (YYYY-MM-DD).",
        )

    def handle(self, *args, **options):
        as_of_value = options.get("as_of")

        if as_of_value:
            as_of = parse_date(as_of_value)

            if as_of is None:
                raise CommandError(
                    "Invalid date. Use YYYY-MM-DD, for example 2026-10-22."
                )
        else:
            as_of = date.today()

        result = generate_monthly_rent_records(as_of=as_of)

        self.stdout.write(
            self.style.SUCCESS(
                f"Rent generation completed through {as_of}."
            )
        )
        self.stdout.write(
            f"New records created: {result['created']}"
        )
        self.stdout.write(
            f"Records already existing: {result['already_existing']}"
        )

