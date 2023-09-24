import json
import boto3

# Clients

dynamodb_client = boto3.client('dynamodb')

lambda_client = boto3.client('lambda')

dynamodbstream_client = boto3.client('dynamodbstreams')

tableName = "Player"

def GetStreamARN():
    
    streams_response = dynamodbstream_client.list_streams(TableName = tableName)
    
    print("Stream ARN " + str(streams_response["Streams"][0]["StreamArn"]))
    
    return streams_response["Streams"][0]["StreamArn"]



def GetLambdaFunctionARN():
    
    lambdaFunction_response = lambda_client.get_function(FunctionName = "ProcessGameDetailsFunction")
    
    print(lambdaFunction_response["Configuration"]["FunctionArn"])
    
    return lambdaFunction_response["Configuration"]["FunctionArn"]
    
    
def CheckWhetherEventSourceMappingAlreadyPresentOrNot(function_name):
    
    list_mappings = lambda_client.list_event_source_mappings(FunctionName = function_name)
    
    if 'EventSourceMappings' in list_mappings:
        
        event_source_mappings = list_mappings['EventSourceMappings']

    # Check if there are existing mappings
    if event_source_mappings:
        
        print("Event source mappings already exist for the Lambda function.")
        return False
        
    else:
        
        print("No event source mappings found for the Lambda function.")
        return True


def createEventSourceMappingForProcessingData():
    
    ## Adding the Trigger to the Lambda Function from the Stream
    
    ## Get the Stream ARN
    stream_arn = GetStreamARN()
    
    ## Get the Process Lambda ARN
    
    function_name = GetLambdaFunctionARN()
    
    ## Attach the Event Source Mapping using Lambda Client
    
    addOrNot = CheckWhetherEventSourceMappingAlreadyPresentOrNot(function_name)
    
    if addOrNot:
        
        response = lambda_client.create_event_source_mapping(
        EventSourceArn=stream_arn,
        FunctionName=function_name,
        StartingPosition='LATEST'
        )
    
        print("The Event Source Mapping between Dynamodb stream and Lambda Function has been established")

    
    
    


def createPlayerTable():
    
    attributeDefinitions = [{
        
        "AttributeName" : "PlayerId",
        "AttributeType" : "N"
    }]
    
    keySchema = [
        {
            "AttributeName" : "PlayerId",
            "KeyType" : "HASH"
        }]
        
    billingMode = "PAY_PER_REQUEST"
    
    streamSpecification = {
        "StreamEnabled" : True,
        'StreamViewType': 'NEW_AND_OLD_IMAGES'
    }
    
    
    available_tables = dynamodb_client.list_tables()["TableNames"]
    
    print("The Available Tables in the dynamodb ")
    print(available_tables)
    
    if tableName not in available_tables:
        
        dynamodb_client.create_table(TableName = tableName, AttributeDefinitions = attributeDefinitions, KeySchema = keySchema, BillingMode = billingMode, StreamSpecification = streamSpecification)
        
        print("Table has been created in the dynamodb table")
    
    else:
        
        print("Table Already exists in the Dynamodb table")


def insertPlayerIntoTable(playerData):
    
    print(playerData)
    
    playerData_dict = json.loads(playerData)
    
    playerId = playerData_dict["playerId"]
    
    playerName = playerData_dict["playerName"]
    
    playerScore = playerData_dict["playerscore"] 
    
    print(playerId, playerName, playerScore)
    
    dynamodb_client.put_item(TableName = tableName, Item = { "PlayerId" : { "N" : str(playerId) }, "PlayerName" : { "S" : playerName }, "PlayerScore" : { "N" : str(playerScore) } })
    
    return "Player has been inserted into the table"
    
    
def CheckPlayerExistsInTable(playerData):
    
    playerData_dict = json.loads(playerData)
    
    playerId = playerData_dict["playerId"]
    
    key = { "PlayerId" : { "N" : str(playerId) }}
    
    getItem_response = dynamodb_client.get_item(TableName = tableName, Key = key)
    
    if "Item" in getItem_response:
        
        print("player exists in the table so proceeding with update")
        
        return True
        
    print("Player doesnot exist in the table. So need to insert into the table")
    
    return False
        
def UpdatePlayerDetail(playerData):
    
    playerData_dict = json.loads(playerData)
    
    playerId = playerData_dict["playerId"]
    
    
    playerscoretobeupdated = playerData_dict["NewScore"]
    
    key = { "PlayerId" : { "N" : str(playerId) }}
    
    update_expression = "SET PlayerScore = :value1"
    
    expression_attribute_values = {
    ':value1': {'N': str(playerscoretobeupdated) }
    }
    
    dynamodb_client.update_item(TableName = tableName, Key = key , UpdateExpression = update_expression, ExpressionAttributeValues = expression_attribute_values)
    
    print("Player details has been updated")
    
def DeletePlayerDetail(playerData):
    
    playerData_dict = json.loads(playerData)
    
    playerId = playerData_dict["playerId"]
    
    key = {"PlayerId" : {"N": str(playerId) }}
    
    dynamodb_client.delete_item(TableName = tableName, Key = key)
    
    print("Player details has been deleted")
    

def lambda_handler(event, context):
    # TODO implement
    
    # Lambda Function will be triggered once the API request has been sent
    try:
        
        httpmethod_type = event["requestContext"]["http"]["method"]
    
        playerdata = event["body"]
    
        print(httpmethod_type)
    
        print(playerdata)
    
        
        createPlayerTable()
        
        createEventSourceMappingForProcessingData()
        
        match httpmethod_type:
            
            case "POST":
                
                print("Player needs to be inserted")
                
                # Insert Player into the Dynamodb Table
                
                print(insertPlayerIntoTable(playerdata))
                
            case "PUT":
                
                print("Player needs to be updated or inserted")
                
                # Update the Player details if player is already present orelse insert the player
                
                if CheckPlayerExistsInTable(playerdata):
                    
                    UpdatePlayerDetail(playerdata)
                    
                else:
                    
                    insertPlayerIntoTable(playerdata)
                
            case "DELETE":
                
                print("Player needs to be deleted")
                
                # Delete the Player detail if player is present in the dynamodb table
        
                if CheckPlayerExistsInTable(playerdata):
                    
                    DeletePlayerDetail(playerdata)
                    
                else:
                    
                    print("Player doesnot exist in the table")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Operation on the Player is successful')
        }
    
    except Exception as e:
        
        print(" Exception has been occured "+ str(e))
        
        print(event)
        
