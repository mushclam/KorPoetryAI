import json
import os
import boto3
import torch

sqs = boto3.client('sqs', region_name='ap-northeast-2')
dynamodb = boto3.client('dynamodb', region_name='ap-northeast-2')

def padding(texts, max_len, start_end=True):
    res = []
    for t in texts:
        if len(t) > max_len + 2:
            t = t[:max_len]
        else:
            t = t + [''] * (max_len - len(t))
        res.append(t)
    return res

def get_message(message):
    attributes = message['messageAttributes']
    tweet_id = attributes['tweetID']['stringValue']
    author_id = attributes['authorID']['stringValue']

    body = json.loads(message['body'])
    input_text = body['input_text']
    morph_text = body['morph_text']
    return tweet_id, author_id, input_text, morph_text

def send_sqs_message(tweet_id, author_id, input_text, output_text):
    # Get the queue
    QueueUrl = os.getenv('SQS_URL')
    
    # Message body
    MessageBody = {
        'input_text': input_text,
        'output_text': output_text
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
        MessageGroupId='to_post',
        MessageDeduplicationId=str(tweet_id),
        MessageBody=MessageBody,
        MessageAttributes=MessageAttributes,
        QueueUrl=QueueUrl
    )
    print(f'Send message {tweet_id}, {author_id}, {input_text}, {output_text}')
    
def store_message(tweet_id, author_id, input_text, output_text):
    table_name = os.getenv('TABLE_NAME')
    dynamodb.put_item(
        TableName=table_name,
        Item={
            'tweet_id': {'S': str(tweet_id)},
            'author_id': {'S': str(author_id)},
            'input_text': {'S': input_text},
            'output_text': {'S': output_text},
            'num_like': {'N': '0'},
            'num_retweet': {'N': '0'}
        }
    )
    print(f'Store data {tweet_id}, {author_id}, {input_text}, {output_text}')

def lambda_handler(event, context):
    tweet_ids = []
    author_ids = []
    input_texts = []
    morph_texts = []
    for message in event['Records']:
        tweet_id, author_id, input_text, morph_text = get_message(message)
        tweet_ids.append(tweet_id)
        author_ids.append(author_id)
        input_texts.append(input_text)
        morph_texts.append(morph_text)

    # morph_texts = str2id(morph_texts)
    # Make batch
    # max_len = os.getenv('MAX_LEN')
    # morph_texts = padding(morph_text, max_len)
    # morph_texts = 
    # morph_texts = torch.tensor(morph_texts)
    # Inference
    output_texts = []
    for mt in morph_texts:
        output = ' '.join(mt)
        output_texts.append(output)
    
    for i in range(len(output_texts)):
        tweet_id = tweet_ids[i]
        author_id = author_ids[i]
        input_text = input_texts[i]
        output_text = output_texts[i]
        send_sqs_message(
            tweet_id,
            author_id,
            input_text,
            output_text
        )
        store_message(
            tweet_id,
            author_id,
            input_text,
            output_text
        )
        
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }