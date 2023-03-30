# FastAPI Lambda API Handler
# using this tutorial https://www.eliasbrange.dev/posts/deploy-fastapi-on-aws-part-1-lambda-api-gateway/
import os
import datetime as dt
from fastapi import FastAPI, Request, Path
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from mangum import Mangum
from helpers import *

# logging for debugging
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

#######################################################################
# Load feeds from Parameter Store
#######################################################################
feeds = get_feeds()
dbname = os.environ['bucket']

# create enumeration of system_ids for validation of query parameters
active_systems = get_system_id_enum(feeds)

#######################################################################
# FastAPI
#######################################################################

app = FastAPI(
    root_path="/", #root_path fix for docs/redoc endpoints
    title="Bus Observatory 2 API",
    description="""The Bus Observatory is a public archive of real-time data on vehicle movements and status, collected from transit systems around the world. This free service is provided by the <a href="https://urban.tech.cornell.edu/">Jacobs Urban Tech Hub</a> at <a href="https://tech.cornell.edu/">Cornell Tech</a>.""",
    version="1.0.0",
    # terms_of_service="http://example.com/terms/",
    contact={
         "name": "Urban Tech Hub",
         "url": "https://urban.tech.cornell.edu/",
         "email": "urbantech@cornell.edu",
         },
    license_info={
        "name": "CC BY-NC 4.0",
        "url": "http://creativecommons.org/licenses/by-nc/4.0/?ref=chooser-v1",
        },
    )

# for home page
# using this tutorial https://levelup.gitconnected.com/building-a-website-starter-with-fastapi-92d077092864
templates = Jinja2Templates(directory="templates")

#FIXME: this isnt working (but templates is)
app.mount("/static", StaticFiles(directory="static"), name="static")


#######################################################################
# custom filters
#######################################################################

def format_number(value):
    return "{:,}".format(value)
templates.env.filters["format_number"] = format_number

#######################################################################
# home page
#######################################################################
@app.get("/", 
         response_class=HTMLResponse,
         include_in_schema=False)
         
async def home(request: Request):

    return templates.TemplateResponse(
        "index.html", {
            "request": request,
            "config": feeds
            }
        )


#######################################################################
# system pages 
#######################################################################

@app.get("/{system_id}/schema", 
         response_class=HTMLResponse,
         include_in_schema=False)

async def schema(request: Request, 
                system_id: str
                 ): 
    return templates.TemplateResponse(
        "schema.html", {
            "request": request,
            "system_id": system_id,
            "config": feeds, # needed for the navbar
            "feed_info": feeds[system_id], # just this one system
            "schema": get_schema(
                system_id
                ), # and the schema fetched from Athena,
            "history": get_system_history(
                dbname,
                feeds[system_id],
                system_id
                ) # and the system history from an athena query# and the routelist from an athena query,
            }
        )

#######################################################################
# by path arguments (one route-hour)
#######################################################################

@app.get("/buses/bulk/{system_id}/{route}/{year}/{month}/{day}/{hour}", 
         response_class=PrettyJSONResponse)
async def fetch_bulk_by_system_route_hour(
    request: Request,
    system_id: str, 
    route: str, 
    year:int = Path(title="Year of service", ge=2011, le=2050), 
    month:int = Path(title="Month of service", ge=1, le=12), 
    day:int = Path(title="Day of service", ge=1, le=31),
    hour:int = Path(title="Hour of service", ge=0, le=23)
    ):

    #convert year/month/day/hour into a start and end ISO 8601 timestamp for bottom and top of hour 
    start = dt.datetime(year,month,day,hour,0,0).isoformat()
    if hour == 23:
        # advance to midnight
        end = dt.datetime(year,month,day+1,0,0,0).isoformat()
    elif hour < 23:
        end = dt.datetime(year,month,day,(hour+1),0,0).isoformat()
    
    # otherwise run query and return results
    return response_packager(
        query_job(feeds, dbname, system_id, route, start, end),
            system_id, route, start, end)

#######################################################################
# get most recent buses for a system_id
#######################################################################
@app.get("/buses/live/{system_id}", 
         response_class=PrettyJSONResponse)
async def fetch_recent_by_system(
    request: Request,
    system_id: str
    ):

    return {"result": "live_query_job endpoint is here"}


    # # # METHOD 1 -- LOAD LATEST PARQUET
    # https://stackoverflow.com/questions/45375999/how-to-download-the-latest-file-of-an-s3-bucket-using-boto3/62864288#62864288
    # return load_latest_parquet(
    #     os.environ['bucket'], 
    #     f"feeds/{system_id}"
    #     )
    
    #METHOD 2 -- ATHENA QUERY
    
    # # generate current time and -75 seconds offset in ISO 8601 formatin ISO 8601 format
    # offset_seconds = 75 #TODO move to stack config
    # start=dt.datetime.now.isoformat()
    # end = dt.timedelta(seconds=offset_seconds)

    # return live_query_job(feeds, dbname, system_id, start, end)

    #TODO next -- run query and return packaged results
    # return fetch_live_by_system_packager(
    #     live_query_job(feeds, dbname, system_id, start, end),
    #     system_id,
    #     start,
    #     end
    #     )


  




#######################################################################
# wrapper for lambda
#######################################################################

handler = Mangum(app)