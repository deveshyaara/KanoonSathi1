import { MongoClient } from 'mongodb';
import { getMongoDBUri } from '../shared/environment';

let client;
let isConnected = false;

export async function connectToMongoDB() {
  try {
    if (!client) {
      const uri = getMongoDBUri();
      client = new MongoClient(uri, {
        maxPoolSize: 10,
        minPoolSize: 5,
        retryWrites: true,
        retryReads: true,
        connectTimeoutMS: 10000,
      });

      await client.connect();
      isConnected = true;
      console.log('Successfully connected to MongoDB');
    }
    return client;
  } catch (error) {
    console.error('MongoDB connection error:', error);
    throw error;
  }
}

export function getMongoClient() {
  if (!client) {
    throw new Error('MongoDB client not initialized. Call connectToMongoDB first.');
  }
  return client;
}

export function isConnectedToDatabase() {
  return isConnected;
}

export async function closeDatabaseConnection() {
  if (client) {
    await client.close();
    client = null;
    isConnected = false;
  }
}