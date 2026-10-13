
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import AdminUserProfile


def send_security_alert(recipients, subject, message):
    recipients = list({
        address.strip()
        for address in recipients
        if address and address.strip()
    })

    if not recipients or not settings.DEFAULT_FROM_EMAIL:
        return

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=True,
        )
    except Exception:
        # Security alerts should not expose sensitive information in errors.
        pass


def alert_message(change_description):
    return (
        "A change was detected in your Property Rental Management account.\n\n"
        f"Change: {change_description}\n"
        f"Time: {timezone.now().astimezone().strftime('%d %b %Y, %I:%M %p %Z')}\n\n"
        "If you made this change, no action is needed.\n"
        "If you did not make this change:\n"
        "1. Change your password immediately.\n"
        "2. Review your account and active sessions.\n"
        "3. Contact your system administrator or support team.\n\n"
        "For your security, this notification does not contain your password."
    )


User = get_user_model()


@receiver(pre_save, sender=User)
def capture_user_security_changes(sender, instance, **kwargs):
    instance._security_previous = None

    if not instance.pk:
        return

    previous = sender.objects.filter(pk=instance.pk).first()

    if previous is not None:
        instance._security_previous = {
            "username": previous.username,
            "email": previous.email,
            "password": previous.password,
        }


@receiver(post_save, sender=User)
def notify_user_security_changes(sender, instance, created, **kwargs):
    previous = getattr(instance, "_security_previous", None)

    if created or not previous:
        return

    old_email = previous["email"]
    new_email = instance.email
    changes = []

    if previous["username"] != instance.username:
        changes.append("Username changed")

    if old_email != new_email:
        changes.append("Email address changed")

    if previous["password"] != instance.password:
        changes.append("Password changed or reset")

    if not changes:
        return

    subject = "Security alert: account information changed"
    message = alert_message(", ".join(changes))

    recipients = [old_email]

    # Also notify the new address after an email change.
    if old_email != new_email:
        recipients.append(new_email)

    send_security_alert(recipients, subject, message)


@receiver(pre_save, sender=AdminUserProfile)
def capture_profile_security_changes(sender, instance, **kwargs):
    instance._previous_mobile_number = None

    if not instance.pk:
        return

    previous = sender.objects.filter(pk=instance.pk).first()

    if previous is not None:
        instance._previous_mobile_number = previous.mobile_number


@receiver(post_save, sender=AdminUserProfile)
def notify_mobile_number_change(sender, instance, created, **kwargs):
    previous_mobile = getattr(
        instance, "_previous_mobile_number", None
    )

    if created or previous_mobile is None:
        return

    if previous_mobile != instance.mobile_number:
        email = instance.user.email

        send_security_alert(
            [email],
            "Security alert: mobile number changed",
            alert_message("Mobile number changed"),
        )
