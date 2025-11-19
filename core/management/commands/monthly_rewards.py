"""
Management command to assign monthly rewards to top students.
Run this command at the end of each month (e.g., via cron job).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.utils import assign_monthly_rewards


class Command(BaseCommand):
    help = 'Assign monthly reward points to top students in each group'

    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=str,
            help='Month in YYYY-MM format (default: current month)',
        )

    def handle(self, *args, **options):
        month_str = options.get('month')
        
        if month_str:
            try:
                from datetime import datetime
                target_month = datetime.strptime(month_str, '%Y-%m')
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid month format. Use YYYY-MM (e.g., 2024-01)')
                )
                return
        else:
            target_month = timezone.now()
        
        self.stdout.write(f'Processing monthly rewards for {target_month.strftime("%B %Y")}...')
        
        stats = assign_monthly_rewards(target_month)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nMonthly rewards assigned successfully!\n'
                f'Groups processed: {stats["groups_processed"]}\n'
                f'Students rewarded: {stats["students_rewarded"]}\n'
                f'Total points awarded: {stats["points_awarded"]}'
            )
        )

