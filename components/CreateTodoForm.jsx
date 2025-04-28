'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { getBackendUrl } from '../utils/shared/environment';

export default function CreateTodoForm() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title) return;

    try {
      setIsSubmitting(true);
      const backendUrl = getBackendUrl(true);
      
      const response = await fetch(`${backendUrl}/api/todos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ 
          title, 
          description, 
          completed: isComplete // Match the field name expected by the backend
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create todo: ${response.status} ${response.statusText}`);
      }
      
      // Reset form
      setTitle('');
      setDescription('');
      setIsComplete(false);
      
      // Refresh the page to show the new todo
      router.refresh();
      
    } catch (error) {
      console.error('Error creating todo:', error);
      alert(`Failed to create todo: ${error.message || 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Create New Todo</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Title *
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
            required
          />
        </div>
        
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
            rows={3}
          />
        </div>
        
        <div className="flex items-center">
          <input
            type="checkbox"
            id="isComplete"
            checked={isComplete}
            onChange={(e) => setIsComplete(e.target.checked)}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded"
          />
          <label htmlFor="isComplete" className="ml-2 block text-sm text-gray-700">
            Mark as complete
          </label>
        </div>
        
        <button
          type="submit"
          disabled={isSubmitting || !title}
          className={`w-full py-2 px-4 rounded-md font-medium ${
            isSubmitting || !title
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {isSubmitting ? 'Creating...' : 'Create Todo'}
        </button>
      </form>
    </div>
  );
}