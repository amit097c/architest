import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Collection, SavedTest } from '@/lib/types';
import { TestStorageService } from '@/lib/storage-service';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import CollectionModal from '@/components/modals/CollectionModal';

const CollectionsSection: React.FC = () => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [tests, setTests] = useState<SavedTest[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCollection, setEditingCollection] = useState<Collection | undefined>();
  const [loading, setLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        await Promise.all([loadCollections(), loadTests()]);
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, []);

  const loadCollections = async () => {
    try {
      const collectionsData = await TestStorageService.getAllCollections();
      setCollections(collectionsData);
    } catch (error) {
      console.error('Error loading collections:', error);
    }
  };

  const loadTests = async () => {
    try {
      const testsData = await TestStorageService.getAllTests();
      setTests(testsData);
    } catch (error) {
      console.error('Error loading tests:', error);
    }
  };

  const handleCreateCollection = () => {
    setEditingCollection(undefined);
    setIsModalOpen(true);
  };

  const handleEditCollection = (collection: Collection) => {
    setEditingCollection(collection);
    setIsModalOpen(true);
  };

  const handleSaveCollection = async (collection: Collection) => {
    setLoading(true);
    try {
      if (editingCollection) {
        await TestStorageService.updateCollection(collection.id || '', collection);
      } else {
        await TestStorageService.createCollection(collection);
      }
      setIsModalOpen(false);
      await loadCollections();
    } catch (error) {
      console.error('Error saving collection:', error);
      alert('Error saving collection. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCollection = async (id: string) => {
    if (confirm('Are you sure you want to delete this collection? Tests in this collection will not be deleted.')) {
      setLoading(true);
      try {
        await TestStorageService.deleteCollection(id);
        await loadCollections();
      } catch (error) {
        console.error('Error deleting collection:', error);
        alert('Error deleting collection. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  };

  const getTestCountByCollection = (collectionId: string) => {
    return tests.filter(test => test.collectionId === collectionId).length;
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <p>Loading collections...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Collections</h2>
        <Button onClick={handleCreateCollection} disabled={loading}>
          Create Collection
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Collection Cards */}
        {collections.map(collection => (
          <Card 
            key={collection.id} 
            className={`cursor-pointer hover:border-primary/20 transition-all ${collection.color}`}
            onClick={() => navigate(`/collection/${collection.id}`)}
          >
            <CardHeader>
              <CardTitle>{collection.name}</CardTitle>
            </CardHeader>
            <CardContent>
              {collection.description && (
                <p className="text-muted-foreground text-sm">{collection.description}</p>
              )}
            </CardContent>
            <CardFooter className="justify-between">
              <span className="text-sm font-medium">
                {getTestCountByCollection(collection.id || '')} tests
              </span>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleEditCollection(collection);
                  }}
                  disabled={loading}
                >
                  Edit
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteCollection(collection.id || '');
                  }}
                  disabled={loading}
                >
                  Delete
                </Button>
              </div>
            </CardFooter>
          </Card>
        ))}
      </div>

      {isModalOpen && (
        <CollectionModal
          collection={editingCollection}
          onSave={handleSaveCollection}
          onCancel={() => setIsModalOpen(false)}
          isLoading={loading}
        />
      )}
    </div>
  );
};

export default CollectionsSection; 