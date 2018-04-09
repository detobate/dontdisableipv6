#!/usr/bin/env python3
from twython import Twython, TwythonStreamer
from twitter_keys import *
import queue
import threading
import time
import random


key_words = ('disable IPv6', 'try disabling IPv6', 'turn off IPv6')
ignore_words = ('don\'t', 'dont', 'shouldn\'t')
dont_urls = ('http://techgenix.com/dont-disable-ipv6/',
             'https://biztechmagazine.com/article/2012/03/should-you-disable-ipv6-windows-7-pc',
             'https://support.microsoft.com/en-us/help/929852/how-to-disable-ipv6-or-its-components-in-windows',
             'https://blogs.technet.microsoft.com/netro/2010/11/24/arguments-against-disabling-ipv6/',
             'https://blogs.technet.microsoft.com/ipv6/2007/11/08/disabling-ipv6-doesnt-help/',
             'https://blogs.technet.microsoft.com/askpfeplat/2013/06/16/ipv6-for-the-windows-administrator-why-you-need-to-care-about-ipv6/',
             'https://blogs.technet.microsoft.com/jlosey/2011/02/02/why-you-should-leave-ipv6-alone/',
             'https://serverfault.com/questions/880537/disadvantage-of-disabling-ipv6',
             'https://www.reddit.com/r/sysadmin/comments/2pewpo/disable_ipv6_and_lose_the_checkmark/')

reply_msg = 'Please don\'t disable IPv6, it will break things. #DontDisableIPv6'

our_twitter_id = 983281983513088000
debug = True


class MyStreamer(TwythonStreamer):

    def on_success(self, data):
        if debug:
            print('Found tweet: "%s"' % str(data['text']))
        q.put(data)

    def on_error(self, status_code, data):
        print('Twitter error %s - %s' % (status_code, data))


def start_twitter():
    stream = MyStreamer(APP_KEY, APP_SECRET, ACCESS_KEY, ACCESS_SECRET)
    stream.statuses.filter(track=','.join(key_words))

def start_twitter_thread():
    t = threading.Thread(target=start_twitter)
    t.daemon = True
    t.start()
    print('Twitter listener thread started')


def ignore_tweet(tweet, ignore_words):
    """ Checks Tweet for words that we want to ignore """
    ignore = False
    for word in tweet.split(' '):
        if word.lower() in [x.lower() for x in ignore_words]:
            ignore = True

    return(ignore)


def reply(tweet, twitter):

    msg = '%s\n%s' % (reply_msg, random.choice(dont_urls))
    if debug:
        print('Replying to tweet_id: %i with "%s"' % (tweet['id'], msg))

    twitter.update_status(status=msg, in_reply_to_status_id=tweet['id'], auto_populate_reply_metadata='true')





def main():

    # Create a globally available queue that our twitter thread can add to
    global q
    q = queue.Queue(42)
    print('Starting Twitter Listener')
    start_twitter_thread()

    twitter = Twython(APP_KEY, APP_SECRET, ACCESS_KEY, ACCESS_SECRET)

    while True:
        if q.empty():
            time.sleep(1)
        else:
            tweet = q.get()
            if tweet['user']['id'] != str(our_twitter_id) and ignore_tweet(tweet['text'], ignore_words) is False:
                if debug:
                    print('Offending tweet: "%s"' % tweet['text'])
                    print('Tweet ID: %i from user: @%s with user ID: %i' % (tweet['id'], tweet['user']['screen_name'], tweet['user']['id']))

                reply(tweet, twitter)

            elif debug:
                print('Ignoring tweet: "%s"' % tweet['text'])
            time.sleep(1)


if __name__ == '__main__':
    main()
