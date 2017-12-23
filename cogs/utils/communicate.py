import os
from requests_oauthlib import OAuth1Session
from cogs.utils.utils import logify_exception_info
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialApp, SocialToken

class Twitter:
    def __init__(self, uid, log):
        self.url = 'https://api.twitter.com/1.1/statuses/update.json'
        self.uid = uid
        self.log_item = log
        self.socialapp = SocialApp.objects.get_current('twitter')

    def log(self, *args):
        for a in args:
            self.log_item.message += "{}\n".format(a)
        self.log_item.save()

    def tweet(self, message):
        try:
            if not self.socialapp:
                self.log("No Twitter app found so I am unable to Tweet")
                return False
            socialtoken = SocialToken.objects.get(account__uid=self.uid, account__provider=self.socialapp.provider)
            twitter = OAuth1Session(
                self.socialapp.client_id,
                client_secret=self.socialapp.secret,
                resource_owner_key=socialtoken.token,
                resource_owner_secret=socialtoken.token_secret
            )

            tweet_params = {
                'status': message,
            }
            r = twitter.post(self.url, params=tweet_params)
            return r.json()
        except Exception as e:
            self.log("Error tweeting", logify_exception_info(), e)
            return None
