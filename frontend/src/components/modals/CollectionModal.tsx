import React, { useState } from 'react';
import { Collection } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';

interface CollectionModalProps {
  collection?: Collection; // If provided, we're editing an existing collection
  onSave: (collection: Collection) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const COLORS = [
  'bg-red-100',
  'bg-orange-100',
  'bg-yellow-100',
  'bg-green-100',
  'bg-blue-100',
  'bg-indigo-100',
  'bg-purple-100',
  'bg-pink-100',
  'bg-gray-100',
];

const CollectionModal: React.FC<CollectionModalProps> = ({
  collection,
  onSave,
  onCancel,
  isLoading = false
}) => {
  const [name, setName] = useState(collection?.name || '');
  const [description, setDescription] = useState(collection?.description || '');
  const [color, setColor] = useState(collection?.color || COLORS[0]);
  const [error, setError] = useState('');

  const handleSave = () => {
    if (!name.trim()) {
      setError('Collection name is required');
      return;
    }

    const updatedCollection: Collection = {
      id: collection?.id || crypto.randomUUID(),
      name: name.trim(),
      description: description.trim() || undefined,
      createdAt: collection?.createdAt || new Date(),
      color
    };

    console.log(updatedCollection);

    onSave(updatedCollection);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>{collection ? 'Edit Collection' : 'Create Collection'}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Collection Name*</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
              placeholder="Enter collection name"
              disabled={isLoading}
            />
            {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
              placeholder="Enter collection description (optional)"
              rows={3}
              disabled={isLoading}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Color</label>
            <div className="flex flex-wrap gap-2">
              {COLORS.map((bgColor) => (
                <button
                  key={bgColor}
                  className={`w-8 h-8 rounded-full ${bgColor} border-2 ${
                    color === bgColor ? 'border-primary' : 'border-transparent'
                  }`}
                  onClick={() => setColor(bgColor)}
                  type="button"
                  disabled={isLoading}
                />
              ))}
            </div>
          </div>
        </CardContent>
        <CardFooter className="justify-end space-x-2">
          <Button variant="outline" onClick={onCancel} disabled={isLoading}>Cancel</Button>
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? 'Saving...' : (collection ? 'Update' : 'Create')}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default CollectionModal; 