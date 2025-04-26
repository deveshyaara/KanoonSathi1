import { MongoClient } from 'mongodb';

if (!process.env.MONGODB_URI) {
  throw new Error('Invalid/Missing environment variable: "MONGODB_URI"');
}

const uri = process.env.MONGODB_URI;
const options = {
  maxPoolSize: 10,
  minPoolSize: 5,
  retryWrites: true,
  retryReads: true,
  connectTimeoutMS: 10000,
  socketTimeoutMS: 45000,
};

let client;
let clientPromise;
let isConnected = false;

async function connectToDatabase() {
  try {
    if (!client) {
      client = new MongoClient(uri, options);
      
      // Add comprehensive event listeners for connection monitoring
      client.on('connectionPoolCreated', () => {
        console.log('MongoDB connection pool created');
        isConnected = true;
      });

      client.on('connectionPoolClosed', () => {
        console.log('MongoDB connection pool closed');
        isConnected = false;
      });

      client.on('connectionCreated', () => {
        console.log('MongoDB connection created');
      });

      client.on('error', (error) => {
        console.error('MongoDB connection error:', error);
        isConnected = false;
        // Attempt to reconnect with exponential backoff
        setTimeout(async () => {
          try {
            await reconnectWithBackoff(1);
          } catch (err) {
            console.error('Reconnection failed:', err);
          }
        }, 1000);
      });

      await client.connect();
    }
    return client;
  } catch (error) {
    console.error('Failed to connect to MongoDB:', error);
    throw error;
  }
}

// Exponential backoff reconnection strategy
async function reconnectWithBackoff(attempt) {
  const maxAttempts = 5;
  const baseDelay = 1000; // 1 second
  
  if (attempt > maxAttempts) {
    throw new Error('Max reconnection attempts reached');
  }

  try {
    if (client) {
      await client.close();
    }
    client = new MongoClient(uri, options);
    await client.connect();
    console.log('Successfully reconnected to MongoDB');
    isConnected = true;
    return client;
  } catch (error) {
    const delay = baseDelay * Math.pow(2, attempt - 1);
    console.log(`Reconnection attempt ${attempt} failed. Retrying in ${delay}ms...`);
    await new Promise(resolve => setTimeout(resolve, delay));
    return reconnectWithBackoff(attempt + 1);
  }
}

// Development vs production initialization
if (process.env.NODE_ENV === 'development') {
  if (!global._mongoClientPromise) {
    global._mongoClientPromise = connectToDatabase();
  }
  clientPromise = global._mongoClientPromise;
} else {
  clientPromise = connectToDatabase();
}

export default clientPromise;

// Helper function to get database instance
export async function getDatabase() {
  const client = await clientPromise;
  return client.db(process.env.MONGODB_DB_NAME || 'kanoonsathi');
}

// Connection status checker
export function isConnectedToDatabase() {
  return isConnected;
}

// Cleanup function for graceful shutdown
export async function closeDatabaseConnection() {
  if (client) {
    await client.close();
    client = null;
    clientPromise = null;
    isConnected = false;
    if (process.env.NODE_ENV === 'development') {
      global._mongoClientPromise = null;
    }
  }
}