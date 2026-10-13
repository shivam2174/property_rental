
from datetime import date

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

from core.models import Invoice
from core.views import get_invoice_cash_balance


class Command(BaseCommand):
    help = "Email tenants about overdue invoices with unpaid balances."

    def handle(self, *args, **options):
        today = date.today()

        invoices = (
            Invoice.objects
            .filter(
                payment_due_date__lt=today,
            )
            .exclude(status__in=["paid", "cancelled"])
            .select_related("tenant")
            .order_by("payment_due_date")
        )

        sent = 0
        skipped = 0

        for invoice in invoices:
            balance = get_invoice_cash_balance(invoice)

            # Never remind a tenant whose net payable balance is zero.
            if balance <= 0:
                skipped += 1
                continue

            recipient = (
                getattr(invoice, "tenant_email", "")
                or getattr(invoice.tenant, "email", "")
            )

            if not recipient:
                self.stdout.write(
                    self.style.WARNING(
                        f"Invoice #{invoice.invoice_number}: no tenant email."
                    )
                )
                skipped += 1
                continue

            overdue_days = (today - invoice.payment_due_date).days

            subject = (
                f"Overdue payment reminder — "
                f"Invoice #{invoice.invoice_number}"
            )

            message = (
                f"Dear {invoice.tenant_name or invoice.tenant},\n\n"
                f"This is a reminder that invoice "
                f"#{invoice.invoice_number} is overdue.\n\n"
                f"Due date: {invoice.payment_due_date}\n"
                f"Days overdue: {overdue_days}\n"
                f"Outstanding net payable amount: ₹{balance:,.2f}\n\n"
                "Please arrange payment of the outstanding amount. "
                "If you have already paid, please contact the property "
                "manager so the records can be checked.\n\n"
                "Regards,\nProperty Manager"
            )

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=False,
            )

            sent += 1
            self.stdout.write(
                f"Reminder sent for invoice #{invoice.invoice_number}."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Emails sent: {sent}; skipped: {skipped}."
            )
        )
