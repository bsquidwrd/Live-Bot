# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-14 04:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('livebot', '0017_auto_20170810_1801'),
    ]

    operations = [
        migrations.AlterField(
            model_name='twitchnotification',
            name='message',
            field=models.CharField(max_length=255, verbose_name='Notification Message'),
        ),
    ]
