# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-11 01:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('livebot', '0016_auto_20170805_1001'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscordGuild',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False, verbose_name='Guild ID')),
                ('name', models.CharField(max_length=255, verbose_name='Guild Name')),
            ],
            options={
                'verbose_name': 'Discord Guild',
                'verbose_name_plural': 'Discord Guilds',
            },
        ),
        migrations.RemoveField(
            model_name='discordchannel',
            name='server',
        ),
        migrations.DeleteModel(
            name='DiscordServer',
        ),
        migrations.AddField(
            model_name='discordchannel',
            name='guild',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='livebot.DiscordGuild', verbose_name='Channel Guild'),
            preserve_default=False,
        ),
    ]
