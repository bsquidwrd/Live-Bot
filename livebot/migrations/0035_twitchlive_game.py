# Generated by Django 2.0 on 2019-02-22 17:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('livebot', '0034_twitchnotification_delay_minutes'),
    ]

    operations = [
        migrations.AddField(
            model_name='twitchlive',
            name='game',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='livebot.TwitchGame', verbose_name='Twitch Game'),
        ),
    ]
