"""
db.py

This module handles the MongoDB connection and provides database models for the application.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any, Union, Annotated
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import pymongo
from pydantic import BaseModel, Field, ConfigDict, GetCoreSchemaHandler
from pydantic_core import core_schema

# MongoDB connection
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/architest")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.get_database("architest")

# Collections
tests_collection = db.tests
collections_collection = db.collections
integration_settings_collection = db.integration_settings

# Helper for JSON serialization of ObjectId
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ]),
        ])

# Pydantic models for MongoDB documents
class JiraConfig(BaseModel):
    domain: str
    email: str
    token: str
    project_key: Optional[str] = None

class GitHubConfig(BaseModel):
    token: str
    username: Optional[str] = None
    repo: Optional[str] = None

class IntegrationSettings(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    jira: Optional[JiraConfig] = None
    github: Optional[GitHubConfig] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class SavedTest(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    testSteps: str
    framework: str
    language: str
    script: str
    url: List[str]
    createdAt: datetime = Field(default_factory=datetime.now)
    tags: Optional[List[str]] = []
    collectionId: Optional[str] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class Collection(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

# Database service functions for tests
async def save_test(test_data: Dict) -> Dict:
    """Save a test to the database and return the complete saved object"""
    test_id = test_data.get("id") or test_data.get("_id")
    
    # Convert string ID to ObjectId if needed
    if isinstance(test_id, str) and ObjectId.is_valid(test_id):
        test_id = ObjectId(test_id)
    
    # Handle createdAt date conversion
    if isinstance(test_data.get("createdAt"), str):
        test_data["createdAt"] = datetime.fromisoformat(test_data["createdAt"].replace('Z', '+00:00'))
    
    if test_id:
        # Update existing test
        test_data["_id"] = test_id
        if "id" in test_data:
            del test_data["id"]
        
        await tests_collection.replace_one(
            {"_id": test_id}, 
            test_data, 
            upsert=True
        )
        # Get the updated document
        updated_test = await tests_collection.find_one({"_id": test_id})
        if updated_test:
            updated_test["id"] = str(updated_test.pop("_id"))
        return updated_test
    else:
        # Insert new test - don't use client-provided ID
        if "id" in test_data:
            del test_data["id"]
        
        result = await tests_collection.insert_one(test_data)
        # Get the newly created document
        created_test = await tests_collection.find_one({"_id": result.inserted_id})
        if created_test:
            created_test["id"] = str(created_test.pop("_id"))
        return created_test

async def get_all_tests() -> List[Dict]:
    """Get all tests from the database"""
    cursor = tests_collection.find().sort("createdAt", pymongo.DESCENDING)
    tests = await cursor.to_list(length=None)
    
    # Convert ObjectId to string for JSON serialization
    for test in tests:
        test["id"] = str(test.pop("_id"))
    
    return tests

async def get_test_by_id(id: str) -> Optional[Dict]:
    """Get a test by ID"""
    if not ObjectId.is_valid(id):
        return None
        
    test = await tests_collection.find_one({"_id": ObjectId(id)})
    if test:
        test["id"] = str(test.pop("_id"))
    return test

async def delete_test(id: str) -> bool:
    """Delete a test by ID"""
    if not ObjectId.is_valid(id):
        return False
        
    result = await tests_collection.delete_one({"_id": ObjectId(id)})
    return result.deleted_count > 0

async def update_test(id: str, updates: Dict) -> bool:
    """Update a test by ID"""
    if not ObjectId.is_valid(id):
        return False
        
    result = await tests_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": updates}
    )
    return result.modified_count > 0

# Database service functions for collections
async def create_collection(collection_data: Dict) -> str:
    """Create a new collection"""
    result = await collections_collection.insert_one(collection_data)
    return str(result.inserted_id)

async def get_all_collections() -> List[Dict]:
    """Get all collections"""
    cursor = collections_collection.find().sort("createdAt", pymongo.DESCENDING)
    collections = await cursor.to_list(length=None)
    
    # Convert ObjectId to string for JSON serialization
    for collection in collections:
        collection["id"] = str(collection.pop("_id"))
    
    return collections

async def get_collection_by_id(id: str) -> Optional[Dict]:
    """Get a collection by ID"""
    if not ObjectId.is_valid(id):
        return None
        
    collection = await collections_collection.find_one({"_id": ObjectId(id)})
    if collection:
        collection["id"] = str(collection.pop("_id"))
    return collection

async def update_collection(id: str, updates: Dict) -> bool:
    """Update a collection by ID"""
    if not ObjectId.is_valid(id):
        return False
        
    result = await collections_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": updates}
    )
    return result.modified_count > 0

async def delete_collection(id: str) -> bool:
    """Delete a collection by ID"""
    if not ObjectId.is_valid(id):
        return False
        
    result = await collections_collection.delete_one({"_id": ObjectId(id)})
    
    # Update all tests that were in this collection
    await tests_collection.update_many(
        {"collectionId": id},
        {"$unset": {"collectionId": ""}}
    )
    
    return result.deleted_count > 0

# Database service functions for integration settings
async def get_integration_settings() -> Dict:
    """Get integration settings"""
    settings = await integration_settings_collection.find_one({"_id": "settings"})
    if not settings:
        return {}
    
    if "_id" in settings:
        del settings["_id"]
    
    return settings

async def save_integration_settings(settings: Dict) -> bool:
    """Save integration settings"""
    result = await integration_settings_collection.replace_one(
        {"_id": "settings"},
        {**settings, "_id": "settings"},
        upsert=True
    )
    return True 