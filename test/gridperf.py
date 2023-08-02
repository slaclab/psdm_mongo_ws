import os
import logging
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from gridfs import GridFS

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # Example from Mikhail https://pswww.slac.stanford.edu/calib_ws/cdb_tstx00417/gridfs/6450604a3a7ab9e8b9dc63b2
    MONGODB_URL=os.environ.get("MONGODB_URL", None)
    if not MONGODB_URL:
        print("Please use the enivironment variable MONGODB_URL to configure the calibration database connection.")    
    mongoclient = MongoClient(host=MONGODB_URL, tz_aware=True)
    expdb = mongoclient["cdb_tstx00417"]
    fs = GridFS(expdb)
    startts = datetime.now()
    with fs.get(ObjectId("6450604a3a7ab9e8b9dc63b2")) as blob:
        length = blob.length
        bytesread = 0
        for chunk in iter(lambda: blob.read(8 * 1024 * 1024), b''):
            bytesread = bytesread + len(chunk)
        endts = datetime.now()
        deltamicros = (endts-startts).microseconds
        mBps = ((length/deltamicros)*(1000000.0))/(1024*1024)
        print(f"Length={length} and bytesread={bytesread} in {deltamicros} microseconds bandwidth={mBps}")
