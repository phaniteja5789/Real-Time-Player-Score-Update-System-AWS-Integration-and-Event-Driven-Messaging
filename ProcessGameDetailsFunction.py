import json
import boto3

#Clients

sns_client = boto3.client('sns')

topic_name = "LiveGameScore"

topicArn = "arn:aws:sns:us-east-1:610954562849:LiveGameScore"



def lambda_handler(event, context):
    # TODO implement
    
    operation_name = event["Records"][0]["eventName"]
    
    print(operation_name)
    
    streamdetails = event["Records"][0]["dynamodb"]
    
    print(streamdetails.keys())
    
    message=""
    
    match operation_name:
        
        case "INSERT":
            
            message = "The details of the player inserted into table are with name = "+ str(streamdetails["NewImage"]["PlayerName"]["S"]) + " and score = "+ str(streamdetails["NewImage"]["PlayerScore"]["N"])
            
        case "REMOVE":
            
            player_message = str(streamdetails["OldImage"]["PlayerName"]["S"]) + " and score = "+ str(streamdetails["OldImage"]["PlayerScore"]["N"])
            
            print(player_message)
            
            message = "The details of the player deleted into table are with name = "+ player_message
            
        case "MODIFY":
            
            player_message = str(streamdetails["NewImage"]["PlayerName"]["S"]) + " and score = "+ str(streamdetails["NewImage"]["PlayerScore"]["N"]) + " Old Score Details = "+ str(streamdetails["OldImage"]["PlayerScore"]["N"])
            
            message = "The details of the player deleted into table are with name = "+ player_message
            
            
            
    sns_client.publish(TopicArn = topicArn, Message = message)        
            
            
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Message has been published to the topic')
    }
