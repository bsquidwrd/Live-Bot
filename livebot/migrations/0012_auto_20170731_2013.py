# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-01 03:13
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('livebot', '0011_auto_20170731_2011'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notification',
            options={'verbose_name': 'Notification', 'verbose_name_plural': 'Notifications'},
        ),
    ]
