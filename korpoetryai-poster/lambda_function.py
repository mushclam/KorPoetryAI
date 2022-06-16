import json
import tweepy
import boto3
import os

ssm = boto3.client('ssm', region_name='ap-northeast-2')

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
        
def get_message(message):
    attributes = message['messageAttributes']
    tweet_id = attributes['tweetID']['stringValue']
    # author_id = attributes['authorID']['stringValue']
    
    text = json.loads(message['body'])
    input_text = text['input_text']
    output_text = text['output_text']
    
    return tweet_id, input_text, output_text
        
def post_mention(client, tweet_id, input_text, output_text):
    # author_id = message['author_id']
    # author_username = client.get_user(id=author_id, user_auth=True)[0]['username']
    # footnote = '\n[아직 형태소 분석만 해주고 있습니다.]'
    footnote = ''
    text = input_text + '->\n' + output_text + footnote
    if len(text) > 140:
        text = text[:140]
    client.create_tweet(text=text, in_reply_to_tweet_id=tweet_id)

def lambda_handler(event, context):
    client = twitter_auth()
    for message in event['Records']:
        message = get_message(message)
        post_mention(client, *message)
    print(event)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

