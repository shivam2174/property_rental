from datetime import date
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    LeaseAgreement,
    RenewalReminder,
    LeaseNotification,
)


def get_effective_end_date(agreement):
    """
    Return the latest configured lease end date,
    including both extensions.
    """
    dates = [
        agreement.end_date,
        agreement.extension_1_end_date,
        agreement.extension_2_end_date,
    ]

    valid_dates = [item for item in dates if item is not None]

    if not valid_dates:
        return None

    return max(valid_dates)


def get_reminder_dates(end_date):
    """
    Six-month warning, followed by monthly reminders
    through the lease expiry date.
    """
    first_reminder = end_date - relativedelta(months=6)
    dates = []
    current = first_reminder

    while current <= end_date:
        dates.append(current)
        current = current + relativedelta(months=1)

    # Ensure an expiry-day reminder is included.
    if end_date not in dates:
        dates.append(end_date)

    return dates


class Command(BaseCommand):
    help = "Create and send lease renewal reminders"

    def handle(self, *args, **options):
        today = timezone.localdate()

        created_count = 0
        sent_count = 0
        cancelled_count = 0
        failed_count = 0

        agreements = LeaseAgreement.objects.select_related(
            "tenant",
            "property",
            "property__owner",
        ).prefetch_related("renewal_reminders")

        for agreement in agreements:
            # Terminated leases must not receive reminders.
            if (
                agreement.status == "terminated"
                or agreement.termination_date is not None
            ):
                cancelled_count += RenewalReminder.objects.filter(
                    lease_agreement=agreement,
                    status="pending",
                ).update(status="cancelled")
                continue

            end_date = get_effective_end_date(agreement)

            # No end date means there is no expiry to remind about.
            if end_date is None:
                continue

            # A lease that has already expired needs renewal or
            # extension details updated before reminders resume.
            if end_date < today:
                cancelled_count += RenewalReminder.objects.filter(
                    lease_agreement=agreement,
                    status="pending",
                ).update(status="cancelled")
                continue

            # Cancel pending reminders associated with an older term.
            cancelled_count += RenewalReminder.objects.filter(
                lease_agreement=agreement,
                status="pending",
            ).exclude(
                lease_end_date=end_date,
            ).update(status="cancelled")

            reminder_dates = get_reminder_dates(end_date)

            # Create the scheduled reminders once.
            for reminder_date in reminder_dates:
                if reminder_date == end_date:
                    reminder_type = "expiry"
                elif reminder_date == (
                    end_date - relativedelta(months=6)
                ):
                    reminder_type = "six_months"
                else:
                    reminder_type = "monthly"

                _, created = RenewalReminder.objects.get_or_create(
                    lease_agreement=agreement,
                    lease_end_date=end_date,
                    reminder_date=reminder_date,
                    reminder_type=reminder_type,
                    defaults={"status": "pending"},
                )

                if created:
                    created_count += 1

            # Process reminders due today.
            due_reminders = RenewalReminder.objects.filter(
                lease_agreement=agreement,
                lease_end_date=end_date,
                reminder_date__lte=today,
                status="pending",
            ).order_by("reminder_date")

            for reminder in due_reminders:
                owner = agreement.property.owner
                owner_email = (
                    owner.email.strip()
                    if owner and owner.email
                    else ""
                )

                title = "Lease renewal reminder"
                message = (
                    f"Lease renewal reminder for "
                    f"{agreement.tenant.full_name}. "
                    f"Property: {agreement.property.name}. "
                    f"Lease expiry date: {end_date:%d %b %Y}. "
                    f"Current monthly rent: "
                    f"₹{agreement.monthly_rent:,.2f}."
                )

                try:
                    # Save the in-app notification once.
                    with transaction.atomic():
                        notification, notification_created = (
                            LeaseNotification.objects.get_or_create(
                                reminder=reminder,
                                defaults={
                                    "lease_agreement": agreement,
                                    "title": title,
                                    "message": message,
                                },
                            )
                        )

                        if notification_created:
                            reminder.in_app_created = True
                            reminder.save(
                                update_fields=["in_app_created"]
                            )

                    # Send an email if an owner email is configured.
                    if owner_email and not reminder.email_sent:
                        send_mail(
                            subject=title,
                            message=message,
                            from_email=getattr(
                                settings,
                                "DEFAULT_FROM_EMAIL",
                                None,
                            ),
                            recipient_list=[owner_email],
                            fail_silently=False,
                        )

                        reminder.email_sent = True

                    # Mark as sent after successful processing.
                    reminder.status = "sent"
                    reminder.sent_at = timezone.now()
                    reminder.error_message = ""
                    reminder.save(
                        update_fields=[
                            "email_sent",
                            "status",
                            "sent_at",
                            "error_message",
                        ]
                    )

                    sent_count += 1

                except Exception as exc:
                    reminder.status = "failed"
                    reminder.error_message = str(exc)[:2000]
                    reminder.save(
                        update_fields=[
                            "status",
                            "error_message",
                        ]
                    )
                    failed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Renewal reminder check completed for {today}.\n"
                f"New reminders: {created_count}\n"
                f"Processed reminders: {sent_count}\n"
                f"Cancelled reminders: {cancelled_count}\n"
                f"Failed reminders: {failed_count}"
            )
        )
