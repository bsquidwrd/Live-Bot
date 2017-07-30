from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added

from .models import *
from ..utils import logify_exception_info


@receiver(pre_save, sender=Log)
def generate_log_token(sender, instance, *args, **kwargs):
    if isinstance(instance, Log):
        if instance.message_token is None or instance.message_token == '':
            instance.generate_log_token(save=False)


@receiver(pre_save, sender=Quote)
def generate_quote_id(sender, instance, *args, **kwargs):
    if isinstance(instance, Quote):
        if instance.quote_id is None or instance.quote_id == '':
            instance.generate_quote_id(save=False)


@receiver(post_save, sender=Log)
def email_log(sender, instance, *args, **kwargs):
    if isinstance(instance, Log):
        if instance.email:
            if instance.subject is None or instance.subject == '':
                subject = "Log item needs your attention"
            else:
                subject = instance.subject
            if instance.body is None or instance.body == '':
                body = instance.message
            else:
                body = instance.body

            try:
                divider = '-'*50
                send_mail(
                    subject='{} {}'.format(settings.EMAIL_SUBJECT_PREFIX, subject),
                    message="Message Token: {0}\n\n{1}\n\n{2}\n\n{1}".format(instance.message_token, divider, body),
                    from_email=settings.SERVER_EMAIL,
                    recipient_list=settings.ADMINS
                )
            except Exception as e:
                Log.objects.create(message="Error sending email about log {}\n\n{}".format(logify_exception_info()), message_token='ERROR_SENDING_EMAIL')
