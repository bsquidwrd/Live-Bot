# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-01 00:49
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('livebot', '0007_auto_20170731_1738'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='twitchlive',
            options={'verbose_name': 'Twitch Live', 'verbose_name_plural': 'Twitch Live Instances'},
        ),
    ]