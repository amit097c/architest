import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { TestStorageService } from '@/lib/storage-service';
import { Collection, SavedTest } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent,
  CardFooter
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import CollectionModal from '@/components/modals/CollectionModal';

const CollectionDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [collection, setCollection] = useState<Collection | null>(null);
  const [tests, setTests] = useState<SavedTest[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (id) {
      loadCollection();
      loadCollectionTests();
    }
  }, [id]);

  const loadCollection = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const foundCollection = await TestStorageService.getCollectionById(id);
    setCollection(foundCollection || null);
    } catch (error) {
      console.error('Error loading collection:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCollectionTests = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const collectionTests = await TestStorageService.getTestsByCollectionId(id);
    setTests(collectionTests);
    } catch (error) {
      console.error('Error loading collection tests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTest = async (testId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this test?')) {
      try {
        setLoading(true);
        await TestStorageService.deleteTest(testId);
        await loadCollectionTests();
      } catch (error) {
        console.error('Error deleting test:', error);
        alert('Error deleting test. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleRemoveTestFromCollection = async (testId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      setLoading(true);
      await TestStorageService.removeTestFromCollection(testId);
      await loadCollectionTests();
    } catch (error) {
      console.error('Error removing test from collection:', error);
      alert('Error removing test from collection. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleEditTest = (testId: string) => {
    navigate(`/edit/${testId}`);
  };

  const handleSaveCollection = async (updatedCollection: Collection) => {
    try {
      setLoading(true);
      await TestStorageService.updateCollection(updatedCollection.id, updatedCollection);
    setIsEditModalOpen(false);
      await loadCollection();
    } catch (error) {
      console.error('Error updating collection:', error);
      alert('Error updating collection. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCollection = async () => {
    if (!collection) return;
    
    if (confirm('Are you sure you want to delete this collection? Tests in this collection will not be deleted.')) {
      try {
        setLoading(true);
        await TestStorageService.deleteCollection(collection.id);
      navigate('/collections');
      } catch (error) {
        console.error('Error deleting collection:', error);
        alert('Error deleting collection. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  };

  const filteredTests = tests.filter(test => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    return (
      test.name.toLowerCase().includes(searchLower) || 
      (typeof test.url === 'string' && test.url.toLowerCase().includes(searchLower)) ||
      test.testSteps.toLowerCase().includes(searchLower) ||
      (test.tags && test.tags.some(tag => tag.toLowerCase().includes(searchLower)))
    );
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'bg-green-50 text-green-500';
      case 'failed': return 'bg-red-50 text-red-500';
      default: return 'bg-gray-50 text-gray-500';
    }
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  if (!collection) {
    return (
      <div className="container mx-auto p-6 max-w-6xl">
        <div className="flex justify-center items-center h-64">
          <p>Collection not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      
      <div className={`mb-6 p-6 rounded-lg ${collection.color}`}>
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">{collection.name}</h1>
            {collection.description && (
              <p className="text-muted-foreground mt-2">{collection.description}</p>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/collections')}>
              Back to Collections
            </Button>
            <Button variant="outline" onClick={() => setIsEditModalOpen(true)}>
              Edit Collection
            </Button>
            <Button variant="destructive" onClick={handleDeleteCollection}>
              Delete Collection
            </Button>
          </div>
        </div>
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder="Search tests in this collection..."
          className="w-full px-3 py-2 border rounded-md"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {filteredTests.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-center text-muted-foreground">
            {searchTerm 
              ? 'No tests match your search criteria' 
              : 'No tests in this collection yet.'}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredTests.map(test => (
            <Card 
              key={test.id} 
              className="cursor-pointer hover:border-primary/20 transition-all"
              onClick={() => handleEditTest(test.id)}
            >
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>{test.name}</CardTitle>
                    <CardDescription className="mt-1">
                      {typeof test.url === 'string' 
                        ? test.url 
                        : (test.url && test.url.length > 0 ? test.url[0] : 'No URL')}
                    </CardDescription>
                  </div>
                  <Badge variant="outline" className={getStatusColor(test.status)}>
                    {test.status.charAt(0).toUpperCase() + test.status.slice(1)}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col space-y-2">
                  <div className="text-sm text-muted-foreground">
                    <span className="font-medium">Framework:</span> {test.framework}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <span className="font-medium">Language:</span> {test.language}
                  </div>
                  {test.isApiTest && (
                    <div className="text-sm text-muted-foreground">
                      <span className="font-medium">API Test:</span> {test.apiDetails?.method} {test.apiDetails?.endpoint}
                    </div>
                  )}
                  {test.tags && test.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {test.tags.map(tag => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <div className="text-sm text-muted-foreground">
                  Created: {formatDate(test.createdAt)}
                </div>
                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={(e) => handleRemoveTestFromCollection(test.id, e)}
                  >
                    Remove from Collection
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={(e) => handleDeleteTest(test.id, e)}
                  >
                    Delete
                  </Button>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {isEditModalOpen && collection && (
        <CollectionModal
          collection={collection}
          onSave={handleSaveCollection}
          onCancel={() => setIsEditModalOpen(false)}
        />
      )}
    </div>
  );
};

export default CollectionDetailsPage; 