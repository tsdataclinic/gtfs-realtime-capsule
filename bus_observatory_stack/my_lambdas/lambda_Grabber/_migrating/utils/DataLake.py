import datetime as dt
import boto3
import os

def dump_buses(region,
                bucket,
                system_id,
                positions_df
                ):

    # dump to instance ephemeral storage 
    timestamp = dt.datetime.now().replace(microsecond=0)
    filename=f"{system_id}_{timestamp}.parquet".replace(" ", "_").replace(":", "_")
    
    positions_df.to_parquet(f"/tmp/{filename}", times='int96')

    # upload to S3
    source_path=f"/tmp/{filename}" 
    remote_path=f"lake/{system_id}/incoming/{filename}"  
    session = boto3.Session(region_name=region)
    s3 = session.resource('s3')
    result = s3.Bucket(bucket).upload_file(source_path,remote_path)

    # clean up /tmp
    try:
        os.remove(source_path)
    except:
        pass