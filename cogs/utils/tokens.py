import web.wsgi
import os
from livebot.models import BearerToken

def get_request_headers():
    client_id = os.getenv('TWITCH_LIVE')
    bearer_token = BearerToken.objects.get(expired=False)
    return {
        'Client-ID': client_id,
        'Authorization': 'Bearer {}'.format(bearer_token.access_token),
    }
