import os
from requests_oauthlib import OAuth1Session
from cogs.utils.utils import logify_exception_info
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialToken

class Twitter:
    def __init__(self, uid, log):
        self.url = 'https://api.twitter.com/1.1/statuses/update.json'
        self.uid = uid
        self.log_item = log

    def log(self, *args):
        for a in args:
            self.log_item.message += "{}\n".format(a)
        self.log_item.save()

    def tweet(self, message):
        try:
            socialtoken = SocialToken.objects.get(account__uid=self.uid, account__provider='twitter')
            twitter = OAuth1Session(
                os.environ['LIVE_BOT_TWITTER_CONSUMER_KEY'],
                client_secret=os.environ['LIVE_BOT_TWITTER_CONSUMER_SECRET'],
                resource_owner_key=socialtoken.token,
                resource_owner_secret=socialtoken.token_secret
            )

            tweet_params = {
                'status': message,
            }
            r = twitter.post(self.url, params=tweet_params)
            self.log(r.status_code, r.text)
        except Exception as e:
            self.log("Error tweeting", logify_exception_info(), e)
