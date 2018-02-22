import asyncio
import aiohttp
import os
from cogs.utils import grouper
from django.db.models import Model
import web.wsgi
from livebot.models import TwitchChannel


loop = asyncio.get_event_loop()
session = aiohttp.ClientSession(loop=loop)


async def run_update_twitch_channels():
    while True:
        await update_twitch_channels()
        print("Waiting 60 seconds to check for users updated again...")
        await asyncio.sleep(60)


async def update_twitch_channels():
    headers = {
        'Client-ID': os.environ['TWITCH_CLIENT_ID'],
    }
    base_url = 'https://api.twitch.tv/helix/users'
    twitch_channels = TwitchChannel.objects.all()
    for channels in grouper(twitch_channels, 100):
        payload = []
        for c in channels:
            if c:
                payload.append(('id', str(c.id)))
        response = await session.get(base_url, headers=headers, params=payload)
        data = await response.json()
        for item in data['data']:
            twitch = TwitchChannel.objects.get_or_create(id=item['id'])[0]
            data = {
                'name': item['login'],
                'display_name': item['display_name'],
                'profile_image': item['profile_image_url'],
                'offline_image': item['offline_image_url'],
            }
            new_twitch, save_obj = update_attribute(twitch, data)
            if save_obj:
                new_twitch.save()
                print("Updated {}".format(new_twitch.display_name))


def update_attribute(obj, data):
        """
        Update an attribute on an object with the data passed in. The data key must match an attribute on obj.

        Returns:
            obj : [:class:`django.db.models.Model`]
                Contains the object with the updated values (if any)
            save_obj : [bool]
                Whether or not to save the object because of updates.
                If the object was updated in any way, this is marked as True, else False

        Parameters:
            obj : Required[:class:`django.db.models.Model`]
                The object to be updated
            data : Required[dict]
                The data to update the object with. The field names must match the attribute names of the model
        """
        if not isinstance(obj, Model):
            raise Exception("obj must be a Django Model")
        if not isinstance(data, dict):
            raise Exception("data must be a dict")
        save_obj = False
        for item in data:
            old_value = getattr(obj, item)
            new_value = data[item]
            if old_value != new_value:
                setattr(obj, item, new_value)
                save_obj = True
        return (obj, save_obj)


if __name__ == "__main__":
    print("Starting to populate user info for TwitchChannel objects")
    loop.run_until_complete(run_update_twitch_channels())
