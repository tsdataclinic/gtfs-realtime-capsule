import json
import boto3

def get_config(event, region, bucket, config_object_key):
    
    try:
        system_id = event['queryStringParameters']['system_id']
    except KeyError:
        raise Exception("No system_id specified")
    
    s3 = boto3.resource("s3")
    obj = s3.Object(bucket, config_object_key)
    
    try:
        config = json.load(obj.get()['Body'])[system_id]
        return config, system_id
    
    #FIXME: this isn't actually catching these
    except:
        # this should raise instead?
        return {
            "statusCode": 404,
            "body": json.dumps({
                "message": f"cannot find feed for system_id:{system_id}",
            }),
        } 
