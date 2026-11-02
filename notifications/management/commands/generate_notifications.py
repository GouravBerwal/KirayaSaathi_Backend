
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_date

from notifications.services import generate_notifications


class Command(BaseCommand):
    help = "Generate upcoming and overdue rent/electricity notifications."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days-ahead",
            type=int,
            default=3,
            help="Due date se kitne din pehle reminder banana hai.",
        )
        parser.add_argument(
            "--as-of",
            type=str,
            help="Testing ke liye reference date: YYYY-MM-DD.",
        )

    def handle(self, *args, **options):
        as_of = None

        if options["as_of"]:
            as_of = parse_date(options["as_of"])

            if as_of is None:
                raise CommandError(
                    "--as-of date YYYY-MM-DD format mein dein."
                )

        try:
            result = generate_notifications(
                days_ahead=options["days_ahead"],
                as_of=as_of,
            )
        except ValueError as error:
            raise CommandError(str(error))

        self.stdout.write(
            self.style.SUCCESS(
                f"Notification generation complete. "
                f"Created: {result['created_count']}, "
                f"Reference date: {result['as_of']}, "
                f"Reminder window: {result['days_ahead']} days."
            )
        )
