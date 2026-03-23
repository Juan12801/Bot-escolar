from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import config

client = MongoClient(config.MONGO_URI)
db = client[config.DATABASE_NAME]
collection = db[config.COLLECTION_NAME]


def add_task(user_id: int, username: str, task_name: str, due_date: str) -> str:
    task = {
        "user_id": user_id,
        "username": username,
        "task_name": task_name,
        "due_date": due_date,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "notified_2_days": False,
        "notified_1_day": False
    }
    result = collection.insert_one(task)
    return str(result.inserted_id)


def get_all_tasks() -> list:
    tasks = list(collection.find().sort("due_date", 1))
    for task in tasks:
        task["_id"] = str(task["_id"])
    return tasks


def get_pending_tasks_2_days() -> list:
    target_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    tasks = list(collection.find({
        "due_date": target_date,
        "notified_2_days": False
    }))
    for task in tasks:
        task["_id"] = str(task["_id"])
    return tasks


def get_pending_tasks_1_day() -> list:
    target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    tasks = list(collection.find({
        "due_date": target_date,
        "notified_1_day": False
    }))
    for task in tasks:
        task["_id"] = str(task["_id"])
    return tasks


def delete_task(task_id: str, user_id: int) -> bool:
    try:
        result = collection.delete_one({
            "_id": ObjectId(task_id),
            "user_id": user_id
        })
        return result.deleted_count > 0
    except:
        return False


def mark_notified_2_days(task_id: str):
    collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"notified_2_days": True}}
    )


def mark_notified_1_day(task_id: str):
    collection.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"notified_1_day": True}}
    )


def get_task_by_id(task_id: str):
    try:
        task = collection.find_one({"_id": ObjectId(task_id)})
        if task:
            task["_id"] = str(task["_id"])
        return task
    except:
        return None
