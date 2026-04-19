from pymongo import MongoClient


class MongoState:
    client: MongoClient | None = None
    db = None


mongo = MongoState()


def init_mongo(app):
    mongo.client = MongoClient(app.config["MONGODB_URI"])
    mongo.db = mongo.client[app.config["MONGODB_DB"]]
