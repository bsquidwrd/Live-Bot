# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-30 19:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('livebot', '0005_auto_20170730_1222'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='success',
            field=models.BooleanField(default=False, verbose_name='Success'),
        ),
        migrations.AddField(
            model_name='notification',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Timestamp'),
        ),
    ]
