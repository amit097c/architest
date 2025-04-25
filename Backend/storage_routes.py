"""
storage_routes.py

This module provides API routes for managing saved tests, collections, and integration settings.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Optional
import db
from pydantic import BaseModel
from datetime import datetime
import json

router = APIRouter()

# Models for request/response
class TestDataRequest(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    testSteps: str
    framework: str
    language: str
    testScript: str
    status: str
    url: str
    createdAt: Optional[datetime] = None
    tags: Optional[List[str]] = []
    collectionId: Optional[str] = None

class CollectionRequest(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    createdAt: Optional[datetime] = None
    color: Optional[str] = None

class TagRequest(BaseModel):
    tag: str

# Test routes
@router.post("/api/tests", response_model=Dict)
async def save_test(test: TestDataRequest):
    """
    Save a test to the database.
    If the test has an ID, it will be updated, otherwise a new test will be created.
    """
    try:
        test_data = test.dict()
        saved_test = await db.save_test(test_data)
        return saved_test
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/tests", response_model=List)
async def get_all_tests():
    """Get all saved tests"""
    try:
        tests = await db.get_all_tests()
        return tests
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/tests/{test_id}", response_model=Dict)
async def get_test_by_id(test_id: str):
    """Get a test by ID"""
    print(test_id)
    test = await db.get_test_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test

@router.delete("/api/tests/{test_id}", response_model=Dict)
async def delete_test(test_id: str):
    """Delete a test by ID"""
    success = await db.delete_test(test_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test not found")
    return {"success": True}

@router.patch("/api/tests/{test_id}", response_model=Dict)
async def update_test(test_id: str, updates: Dict = Body(...)):
    """Update a test by ID"""
    success = await db.update_test(test_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Test not found or no changes made")
    return {"success": True}

@router.post("/api/tests/{test_id}/tags", response_model=Dict)
async def add_tag_to_test(test_id: str, tag_request: TagRequest):
    """Add a tag to a test"""
    test = await db.get_test_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    tags = test.get("tags", [])
    if tag_request.tag not in tags:
        tags.append(tag_request.tag)
        await db.update_test(test_id, {"tags": tags})
    
    return {"success": True}

@router.delete("/api/tests/{test_id}/tags/{tag}", response_model=Dict)
async def remove_tag_from_test(test_id: str, tag: str):
    """Remove a tag from a test"""
    test = await db.get_test_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    tags = test.get("tags", [])
    if tag in tags:
        tags.remove(tag)
        await db.update_test(test_id, {"tags": tags})
    
    return {"success": True}

# Collection routes
@router.post("/api/collections", response_model=Dict)
async def create_collection(collection: CollectionRequest):
    """Create a new collection"""
    try:
        collection_data = collection.dict()
        collection_id = await db.create_collection(collection_data)
        return {"success": True, "id": collection_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/collections", response_model=List)
async def get_all_collections():
    """Get all collections"""
    try:
        collections = await db.get_all_collections()
        return collections
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/collections/{collection_id}", response_model=Dict)
async def get_collection_by_id(collection_id: str):
    """Get a collection by ID"""
    collection = await db.get_collection_by_id(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection

@router.patch("/api/collections/{collection_id}", response_model=Dict)
async def update_collection(collection_id: str, updates: Dict = Body(...)):
    """Update a collection by ID"""
    success = await db.update_collection(collection_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Collection not found or no changes made")
    return {"success": True}

@router.delete("/api/collections/{collection_id}", response_model=Dict)
async def delete_collection(collection_id: str):
    """Delete a collection by ID"""
    success = await db.delete_collection(collection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Collection not found")
    return {"success": True}

@router.get("/api/collections/{collection_id}/tests", response_model=List)
async def get_tests_by_collection_id(collection_id: str):
    """Get all tests in a collection"""
    try:
        tests = await db.get_all_tests()
        collection_tests = [test for test in tests if test.get("collectionId") == collection_id]
        return collection_tests
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/tests/{test_id}/collection/{collection_id}", response_model=Dict)
async def add_test_to_collection(test_id: str, collection_id: str):
    """Add a test to a collection"""
    # Verify both test and collection exist
    test = await db.get_test_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    collection = await db.get_collection_by_id(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Update the test with the collection ID
    success = await db.update_test(test_id, {"collectionId": collection_id})
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update test")
    
    return {"success": True}

@router.delete("/api/tests/{test_id}/collection", response_model=Dict)
async def remove_test_from_collection(test_id: str):
    """Remove a test from its collection"""
    test = await db.get_test_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Remove the collection ID from the test
    if test.get("collectionId"):
        success = await db.update_test(test_id, {"collectionId": None})
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update test")
    
    return {"success": True}

# Integration settings routes
@router.get("/api/integration-settings", response_model=Dict)
async def get_integration_settings():
    """Get integration settings"""
    try:
        settings = await db.get_integration_settings()
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/integration-settings", response_model=Dict)
async def save_integration_settings(settings: Dict = Body(...)):
    """Save integration settings"""
    try:
        await db.save_integration_settings(settings)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/integration-settings/jira", response_model=Dict)
async def save_jira_config(jira_config: Dict = Body(...)):
    """Save Jira integration config"""
    try:
        settings = await db.get_integration_settings()
        settings["jira"] = jira_config
        await db.save_integration_settings(settings)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/integration-settings/github", response_model=Dict)
async def save_github_config(github_config: Dict = Body(...)):
    """Save GitHub integration config"""
    try:
        settings = await db.get_integration_settings()
        settings["github"] = github_config
        await db.save_integration_settings(settings)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/integration-settings/jira", response_model=Dict)
async def clear_jira_config():
    """Clear Jira integration config"""
    try:
        settings = await db.get_integration_settings()
        if "jira" in settings:
            del settings["jira"]
            await db.save_integration_settings(settings)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/integration-settings/github", response_model=Dict)
async def clear_github_config():
    """Clear GitHub integration config"""
    try:
        settings = await db.get_integration_settings()
        if "github" in settings:
            del settings["github"]
            await db.save_integration_settings(settings)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 