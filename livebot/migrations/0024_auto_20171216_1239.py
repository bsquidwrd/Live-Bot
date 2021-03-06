# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-12-16 20:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('livebot', '0023_auto_20171216_1229'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='webhooknotification',
            name='live',
        ),
        migrations.AddField(
            model_name='webhooknotification',
            name='processed',
            field=models.BooleanField(default=False, verbose_name='Processed'),
        ),
        migrations.AddField(
            model_name='webhooknotification',
            name='twitch',
            field=models.ForeignKey(default=22812120, on_delete=django.db.models.deletion.CASCADE, to='livebot.TwitchChannel', verbose_name='Twitch Channel'),
            preserve_default=False,
        ),
    ]
