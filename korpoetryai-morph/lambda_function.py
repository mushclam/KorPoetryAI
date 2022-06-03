import json
import os
import boto3
from konlpy.tag import Mecab

sqs = boto3.client('sqs', region_name='ap-northeast-2')

def get_message(message):
    attributes = message['messageAttributes']
    tweet_id = attributes['tweetID']['stringValue']
    author_id = attributes['authorID']['stringValue']
    text = message['body']
    return tweet_id, author_id, text

def send_sqs_message(tweet_id, author_id, input_text, morph_text):
    # Get the queue
    QueueUrl = os.getenv('SQS_URL')
    
    # Message body
    MessageBody = {
        'input_text': input_text,
        'morph_text': morph_text
    }
    MessageBody = json.dumps(MessageBody)

    # Put attributes in SQS
    MessageAttributes={
        'tweetID': {
            'DataType': 'String',
            'StringValue': str(tweet_id)
        },
        'authorID': {
            'DataType': 'String',
            'StringValue': str(author_id)
        }
    }
    sqs.send_message(
        MessageGroupId='to_inference',
        MessageDeduplicationId=str(tweet_id),
        MessageBody=MessageBody,
        MessageAttributes=MessageAttributes,
        QueueUrl=QueueUrl
    )
    print(f'Send message {tweet_id}, {author_id}, {input_text}, {morph_text}')

def lambda_handler(event, context):
    # for async data processing
    message = event['Records'][0]
    tweet_id, author_id, text = get_message(message)
    
    # Morph
    print(f'Morphing start: {text}')
    tagger = Mecab()
    morph_text = tagger.morphs(text)
    print('Morphing end.')
    
    # Input inference waiting queue
    send_sqs_message(
        tweet_id,
        author_id,
        text,
        morph_text
    )
        
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
