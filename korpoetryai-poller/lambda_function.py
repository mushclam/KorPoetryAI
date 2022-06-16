import tweepy
import json
import os
import re
import boto3

ssm = boto3.client('ssm', region_name='ap-northeast-2')
sqs = boto3.client('sqs', region_name='ap-northeast-2')

def twitter_auth():
    try:
        # client = tweepy.Client(
        #     consumer_key=ssm.get_parameter(Name='twitter_api_key', WithDecryption=True)['Parameter']['Value'],
        #     consumer_secret=ssm.get_parameter(Name='twitter_api_secret', WithDecryption=True)['Parameter']['Value'],
        #     access_token=ssm.get_parameter(Name='twitter_access_token', WithDecryption=True)['Parameter']['Value'],
        #     access_token_secret=ssm.get_parameter(Name='twitter_access_secret', WithDecryption=True)['Parameter']['Value']
        # )
        client = tweepy.Client(
            consumer_key=os.getenv('API_KEY'),
            consumer_secret=os.getenv('API_SECRET'),
            access_token=os.getenv('ACCESS_TOKEN'),
            access_token_secret=os.getenv('ACCESS_SECRET')
        )
        return client
    except Exception as e:
        print(e)
        return None
        
def get_user(client):
    user = client.get_me().data
    user_id = user['id']
    user_name = user['name']
    user_username = user['username']
    return user_id, user_name, user_username
    
def get_mentions(client, user_id, username):
    # get list of recent mentions
    tweet_fields = ['author_id', 'created_at', 'text', 'referenced_tweets']
    newest_id = ssm.get_parameter(Name='twitter_newest_id')['Parameter']['Value']
    # newest_id = '0'
    mentions = client.get_users_mentions(user_id, user_auth=True, tweet_fields=tweet_fields, since_id=newest_id)
    
    meta = mentions.meta
    # check existence of newest tweets
    if meta['result_count'] <= 0:
        print('No newest mentions')
        return None

    # get input text by referenced tweet
    results = []
    for m in mentions.data:
        tweet_id = m['id']
        author_id = m['author_id']
        text = m.data['text']
        print(text)
        # created_at = m['created_at']
        if m['referenced_tweets'] is not None:
            # gather the information of referenced tweets
            ref_tweet_id = m['referenced_tweets'][0]['id']
            ref_tweet = client.get_tweet(ref_tweet_id, user_auth=True)[0]
            if ref_tweet['author_id'] == user_id:
                continue
            text = ref_tweet.data['text']
        text = re.sub('@[\w]+', '', text).strip()
        r = {
            'tweet_id': tweet_id,
            'author_id': author_id,
            'input_text': text
        }
        print(r)
        results.append(r)
        
        # update since_id
        ssm.put_parameter(Name='twitter_newest_id', Value=meta['newest_id'], Overwrite=True)
    return results
    
def send_sqs_message(mention):
    # Get the queue
    QueueUrl = os.getenv('SQS_URL')

    # Put attributes in SQS
    MessageAttributes={
        'tweetID': {
            'DataType': 'String',
            'StringValue': str(mention['tweet_id'])
        },
        'authorID': {
            'DataType': 'String',
            'StringValue': str(mention['author_id'])
        }
    }
    
    sqs.send_message(
        MessageGroupId='to_morph',
        MessageDeduplicationId=str(mention['tweet_id']),
        MessageBody=mention['input_text'],
        MessageAttributes=MessageAttributes,
        QueueUrl=QueueUrl
    ) 
    
def lambda_handler(event, context):
    client = twitter_auth()
    user_id, name, username = get_user(client)
    # Poll mentions to bot
    mentions = get_mentions(client, user_id, username)
    if mentions is not None:
        for mnt in mentions:
            # Send mentions to morph
            send_sqs_message(mnt)
        
    return {
        "statusCode": 200,
        "body": json.dumps(
            {"message": "KorPoetryAI"}
        )
    }
