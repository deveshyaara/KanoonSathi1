import { createClient } from '@/utils/supabase/server';
import { cookies } from 'next/headers';
import Link from 'next/link';
import CreateTodoForm from '@/components/CreateTodoForm';

export default async function TodosPage() {
  const cookieStore = cookies();
  const supabase = createClient(cookieStore);

  // Fetch all todos
  const { data: todos, error } = await supabase
    .from('todos')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) {
    console.error('Error fetching todos:', error);
  }

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Todo List</h1>
        <Link href="/" className="text-blue-600 hover:text-blue-800">
          ← Back to Home
        </Link>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        <div>
          <CreateTodoForm />
        </div>
        
        <div>
          <div className="bg-white shadow-md rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Your Todos</h2>
            
            {error && (
              <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4">
                <p>Error loading todos: {error.message}</p>
              </div>
            )}
            
            {todos && todos.length > 0 ? (
              <ul className="space-y-3">
                {todos.map((todo) => (
                  <li 
                    key={todo.id} 
                    className={`p-3 rounded-md border ${
                      todo.is_complete 
                        ? 'bg-green-50 border-green-200' 
                        : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className={`font-medium ${todo.is_complete ? 'line-through text-gray-500' : ''}`}>
                          {todo.title}
                        </h3>
                        {todo.description && (
                          <p className="text-sm text-gray-600 mt-1">{todo.description}</p>
                        )}
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        todo.is_complete 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {todo.is_complete ? 'Completed' : 'Active'}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">No todos found. Create one to get started!</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}