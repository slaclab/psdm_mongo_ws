# psdm_mongo_ws

This repo contains a simple application that exposes a MongoDB instance as a read only REST service.
### Usage
These examples work against a database `test_db` with a collection `test_coll` with the following data
```
db.test_coll.insertMany([
   { item: "journal", qty: 25, size: { h: 14, w: 21, uom: "cm" }, status: "A" },
   { item: "notebook", qty: 50, size: { h: 8.5, w: 11, uom: "in" }, status: "A" },
   { item: "paper", qty: 100, size: { h: 8.5, w: 11, uom: "in" }, status: "D" },
   { item: "planner", qty: 75, size: { h: 22.85, w: 30, uom: "cm" }, status: "D" },
   { item: "postcard", qty: 45, size: { h: 10, w: 15.25, uom: "cm" }, status: "A" }
]);
```
Get list of databases
```bash
curl -s "http://localhost:5000/"
```

Get collections in a database
```bash
curl -s "http://localhost:5000/test_db"
```

Get object given an object id - URL is of the form *prefix*/`database_name`/`collection_name`/`object_id`.
For example,
```bash
curl -s "http://localhost:5000/test_db/test_coll/5b649a9df59ae00bda110168"
```

Get all objects in a collection - URL is of the form *prefix*/`database_name`/`collection_name`.
For example,
```bash
curl -s "http://localhost:5000/test_db/test_coll"
```

Get all objects matching any number of key value pairs
For example, get objects matching the query `{"item": "planner", "size.uom": "cm"}`
```bash
curl -s "http://localhost:5000/test_db/test_coll?item=planner&size.uom=cm"
```

The previous version of the search may not satisfy all search criteria.
To pass in the search string as is, URL escape it using something like https://meyerweb.com/eric/tools/dencoder/ and pass it as the value of a parameter `query_string`.
For example, querying against the `qty` parameter will not work using name/value pairs because of type mismatches.
That is, we need to query using `{ "item": "planner", "qty": 75 }` but the conversion from HTTP will yield `{ "item": "planner", "qty": "75" }`.
So, URL escape `{ "item": "planner", "qty": 75 }` and pass it as the `query_string` like so
```bash
curl -s "http://localhost:5000/test_db/test_coll?query_string=%7B%20%22item%22%3A%20%22planner%22%2C%20%22qty%22%3A%2075%20%7D%0A"
```

To get documents from GridFS, use the GridFS id. For example, to extract the file with id `5b6893d91ead141643fe3f6a`, use something like so.
```bash
curl -s "http://localhost:5000/test_db/gridfs/5b6893d91ead141643fe3f6a"
```
