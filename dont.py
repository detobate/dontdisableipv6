#!/usr/bin/env python3
from twython import Twython, TwythonStreamer
from twitter_keys import *
import queue
import threading
import time
import random


key_words = ('disable IPv6', 'disabling IPv6', 'turn off IPv6', 'turning off IPv6')
ignore_words = ('#dontdisableipv6', 'don\'t', 'dont', 'do not', 'shouldn\'t', 'should not', 'stop')
dont_urls = {
            'xbox': ['http://xbox.com/ipv6'],
            'windows': [
                'http://techgenix.com/dont-disable-ipv6/',
                'https://biztechmagazine.com/article/2012/03/should-you-disable-ipv6-windows-7-pc',
                'https://support.microsoft.com/en-us/help/929852/how-to-disable-ipv6-or-its-components-in-windows',
                'https://blogs.technet.microsoft.com/netro/2010/11/24/arguments-against-disabling-ipv6/',
                'https://blogs.technet.microsoft.com/ipv6/2007/11/08/disabling-ipv6-doesnt-help/',
                'https://blogs.technet.microsoft.com/askpfeplat/2013/06/16/ipv6-for-the-windows-administrator-why-you-need-to-care-about-ipv6/',
                'https://blogs.technet.microsoft.com/jlosey/2011/02/02/why-you-should-leave-ipv6-alone/',
                'https://www.reddit.com/r/sysadmin/comments/2pewpo/disable_ipv6_and_lose_the_checkmark/',
                'https://docs.microsoft.com/en-us/previous-versions/windows/it-pro/windows-8.1-and-8/hh831730(v=ws.11)#EBE'
                ],
            'generic': [
                'https://serverfault.com/questions/880537/disadvantage-of-disabling-ipv6',
                'https://blogs.cisco.com/enterprise/disable-ipv6',
                'https://superuser.com/questions/1229910/disable-or-enable-ipv6-in-router'
                ]
             }

replies = {
            'windows': ['Windows relies on #IPv6 internally, disabling it will cause issues'],
            'fifa': ['@EA\'s Fifa is notoriously bad at supporting #IPv6 but @XboxSupport still recommends leaving it enabled'],
            'xbox': ['Some Xbox games are poorly written and misbehave on IPv6, but @XboxSupport still recommends leaving it enabled'],
            'faster': ['https://www.howtogeek.com/195062/no-disabling-ipv6-probably-wont-speed-up-your-internet-connection/'],
            'generic': [
                'Please don\'t disable IPv6, it will break things.',
                'You shouldn\'t really disable IPv6, it\'s the future of the internet.',
                'It\'s probably not IPv6\'s fault.',
                'Disabling IPv6 might fix your current problem, but it will cause you more issues in the future.'
                ]
            }

hashtag = '#DontDisableIPv6'
our_twitter_id = 983281983513088000
debug = False
debug_high = False
dry_run = False


class MyStreamer(TwythonStreamer):

    def on_success(self, data):
        if debug:
            print('Found tweet: "%s"' % str(data['text']))
        q.put(data)

    def on_error(self, status_code, data):
        print('Twitter error %s - %s' % (status_code, data))


def start_twitter():
    while True:
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
    for word in tweet:
        if word.lower() in ignore_words:
            ignore = True

    return(ignore)


def reply(tweet, twitter):

    # Try to find a relevant url and msg based on key words
    url = None
    for word in tweet['text'].split():
        if word.lower() in dont_urls.keys() and word != 'generic':
            url = random.choice(dont_urls[word.lower()])
            break
    if url is None:
        url = random.choice(dont_urls['generic'])

    msg = None
    for word in tweet['text'].split():
        if word.lower() in replies.keys() and word != 'generic':
            msg = random.choice(replies[word.lower()])
            break
    if msg is None:
        msg = random.choice(replies['generic'])

    reply_tweet = '%s %s\n%s' % (msg, hashtag, url)

    if debug:
        print('Replying to tweet_id: %i with "%s"' % (tweet['id'], reply_tweet))

    try:
        if not dry_run:
            twitter.update_status(status=reply_tweet, in_reply_to_status_id=tweet['id'], auto_populate_reply_metadata='true')

    except twython.exceptions.TwythonError:
        if debug:
            print('Failed to reply to tweet_id: %i' % tweet['id'])
        pass


def main():

    # Create a globally available queue that our twitter thread can add to
    global q
    q = queue.Queue(42)
    print('Starting Twitter Listener')
    start_twitter_thread()

    twitter = Twython(APP_KEY, APP_SECRET, ACCESS_KEY, ACCESS_SECRET)

    replied_to = []     # List to keep track of who we've replied to recently

    while True:
        if q.empty():
            time.sleep(1)
        else:
            tweet = q.get()

            # Don't test if True, as it's not always present
            if 'retweeted_status' in tweet:
                if debug and debug_high:
                    print('Ignoring Retweet: %s' % tweet)
                elif debug:
                    print('Ignoring Retweet: %s' % tweet['text'])
                pass
            # is_quote_status is always present
            elif tweet['is_quote_status'] is 'False':
                if debug and debug_high:
                    print('Ignoring Quoted Tweet: %s' % tweet)
                elif debug:
                    print('Ignoring Quoted Tweet: %s' % tweet['text'])
                pass

            elif tweet['user']['id'] != our_twitter_id and ignore_tweet(tweet['text'], ignore_words) is False:

                print('Offending tweet: "%s"' % tweet['text'])

                if debug and debug_high:
                    print(tweet)
                elif debug:
                    print('Tweet ID: %i from user: @%s with user ID: %i' % (tweet['id'], tweet['user']['screen_name'], tweet['user']['id']))

                # Update the list of who we've replied to
                if tweet['user']['id'] not in replied_to:
                    replied_to.insert(0, (tweet['user']['id']))
                    reply(tweet, twitter)
                    if len(replied_to) > 5:
                        popped = replied_to.pop()

                elif debug:
                    print('We\'ve already replied to @%s recently. Ignoring' % tweet['user']['screen_name'])

            elif debug:
                print('Ignoring tweet: "%s"' % tweet['text'])
            time.sleep(1)


if __name__ == '__main__':
    main()
