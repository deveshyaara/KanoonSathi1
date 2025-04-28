import React, { useEffect, useState } from 'react';
import { getBackendUrl } from '../utils/shared/environment';

const TodosDemo = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true);
        setError(null);

        // Get backend URL
        const backendUrl = getBackendUrl(true);
        
        // Fetch todos from the API
        const response = await fetch(`${backendUrl}/api/todos`, {
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
          }
        });
        
        if (!response.ok) {
          throw new Error(`Failed to fetch todos: ${response.status} ${response.statusText}`);
        }

        const testData = await response.json();
        setData(testData);
      } catch (err) {
        console.error('Error fetching data from API:', err);
        setError(err.message || 'Failed to load data from API');
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, []);

  return (
    <div className="glossy-card p-6 my-6 w-full max-w-lg mx-auto">
      <h2 className="text-2xl font-semibold mb-4">Todo List Demo</h2>
      
      {isLoading && (
        <div className="flex justify-center items-center my-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
        </div>
      )}

      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 my-4" role="alert">
          <p className="font-bold">Error</p>
          <p>{error.replace(/'/g, "&apos;")}</p>
        </div>
      )}

      {data && data.length > 0 && (
        <div>
          <p className="mb-3">Successfully retrieved todos!</p>
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border border-gray-200">
              <thead className="bg-gray-100">
                <tr>
                  {Object.keys(data[0] || {}).map(key => (
                    <th key={key} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.map((item, i) => (
                  <tr key={i}>
                    {Object.values(item).map((value, j) => (
                      <td key={j} className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!isLoading && !error && (!data || data.length === 0) && (
        <p className="text-gray-500">No todos available. Create one to get started!</p>
      )}
    </div>
  );
};

export default TodosDemo;