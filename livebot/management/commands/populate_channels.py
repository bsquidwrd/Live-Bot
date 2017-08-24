from django.core.management.base import BaseCommand, CommandError
from livebot.models import *
import requests
import random
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    def handle(self, *args, **options):
        channel_ids = [c.id for c in DiscordChannel.objects.filter(guild__id=225471771355250688)]
        secure_random = random.SystemRandom()
        twitch_app = SocialApp.objects.get_current('twitch')
        headers = {
            'Client-ID': twitch_app.client_id,
        }
        r = requests.get('https://api.twitch.tv/kraken/streams/?stream_type=live&limit=100', headers=headers)
        result = r.json()
        for stream in result['streams']:
            if stream is not None:
                if stream['stream_type'] == 'live':
                    try:
                        twitch = TwitchChannel.objects.get_or_create(id=stream['channel']['_id'], name=stream['channel']['name'])[0]
                        notification_args = {
                            'content_type': DiscordChannel.get_content_type(),
                            'object_id': secure_random.choice(channel_ids),
                            'twitch': twitch,
                            'message': '{name} is live and is playing {game}! {url}'
                        }
                        TwitchNotification.objects.get_or_create(**notification_args)
                    except Exception as e:
                        print(e)
