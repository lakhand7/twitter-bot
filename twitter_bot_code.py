import tweepy
import twitter_config
import logging
from datetime import datetime, timedelta

def get_api(api_config):

    auth = tweepy.OAuthHandler(api_config['api_key'], api_config['api_key_secret'])
    auth.set_access_token(api_config['access_token'], api_config['access_token_secret'])

    # Create API object
    api = tweepy.API(auth, wait_on_rate_limit=True,
        wait_on_rate_limit_notify=True)

    try:
        temp = api.verify_credentials()
        logger.info("Authentication OK")
    except:
        logger.error("Error during authentication", exc_info=True)

    return api


def get_timestamp_past_24_hours():

    present = datetime.now()

    DAY = timedelta(days=1)
    past = present - DAY

    return past

def get_tweet_list(timeline, past, retweets=True):

    # for a given @user
    tweet_list = []
    for tweet in timeline:

        # If the tweet is prior to the last 24 hours
        if tweet.created_at < past:
            break
        else:
            # Only proceed if the tweet is directly from the user or a retweet
            if not(tweet.in_reply_to_status_id):

                # If tweet is a RT
                try:
                    tweet = tweet.retweeted_status

                    # if retweets is False, continue
                    if not(retweets):continue

                # pass if it's a direct tweet from the said user
                except: pass

                tweet_list.append([tweet.id_str, tweet.full_text, tweet.retweet_count, tweet.favorite_count])

    return tweet_list

def apply_logic(api, user_name, tweet_list):

    if len(tweet_list) == 0:
        logger.info(f'No tweets from {user_name} fulfil the specified criteria')
        return

    # sort list with key
    # 2-> retweet_count and 3 -> favorite_count
    # get the first tweet after sorting in descending order and then get tweet_id
    max_retweets_id = sorted(tweet_list, key=lambda i:i[2], reverse=True)[0][0]
    max_favorites_id = sorted(tweet_list, key=lambda i:i[3], reverse=True)[0][0]

    # if max_retweets_id and max_favorites_id refer to the same id, retweet one of them
    if max_retweets_id == max_favorites_id:
        _ = api.retweet(int(max_retweets_id))

    else:
        _ = api.retweet(int(max_retweets_id))
        _ = api.retweet(int(max_favorites_id))

def retweet(api, user_name, past, retweets=True):

    tweet_list = []

    # specify the page number
    page_no=1

    # get tweets for the specified user
    timeline = api.user_timeline(user_name, tweet_mode="extended", count=50, page=page_no)

    # the first tweet is created prior to the past datetime
    while timeline[0].created_at > past:

        # append the returned list of tweets
        tweet_list += get_tweet_list(timeline, past, retweets=retweets)

        # Increment page_no counter
        page_no+=1

        # get the next batch of tweets for the specified user
        timeline = api.user_timeline(user_name, tweet_mode="extended", count=50, page=page_no)

    # return tweet_list

    # send to apply_logic func for sorting and other checks
    apply_logic(api, user_name, tweet_list)


if __name__ == '__main__':

    logging.basicConfig(filename='app.log', filemode='w', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

    logger = logging.getLogger()

    api = get_api(twitter_config.api_config)

    past = get_timestamp_past_24_hours()

    for user_name in twitter_config.list_user_names:

        # if empty, then continue
        if user_name is None:
            continue

        try:
            retweet(api, user_name, past, retweets=False)

        # To handle any errors raises while running against a specific user
        #except tweepy.TweepError as e:
        except Exception as e:
            logger.error(f'User Name: {user_name} with Exception: {e}', exc_info=True)
