// deployment-setup.js - Helper script for deploying KanoonSathi
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Read deployment config
const config = JSON.parse(fs.readFileSync('./deployment.config.json', 'utf8'));
const environment = process.env.NODE_ENV || 'development';

console.log(`\n🚀 Setting up KanoonSathi for ${environment} environment\n`);

// Create required directories for backend
const requiredDirs = config.deployment.backend.requiredDirs;
for (const dir of requiredDirs) {
  const dirPath = path.join('./backend', dir);
  if (!fs.existsSync(dirPath)) {
    console.log(`Creating directory: ${dirPath}`);
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

// Verify environment variables are set for production
if (environment === 'production' || environment === 'staging') {
  const requiredVars = [
    'NEXT_PUBLIC_APP_URL',
    'NEXT_PUBLIC_BACKEND_URL',
    'MONGODB_URI'
  ];
  
  const missingVars = requiredVars.filter(varName => !process.env[varName]);
  
  if (missingVars.length > 0) {
    console.error('\n❌ Error: Missing required environment variables:');
    missingVars.forEach(varName => console.error(`   - ${varName}`));
    console.error('\nPlease set these variables in your environment or .env file');
    console.error('You can use .env.example as a template.\n');
    process.exit(1);
  }
}

// Verify package dependencies
try {
  console.log('Verifying backend dependencies...');
  execSync('pip list | findstr pytesseract', { stdio: 'inherit' });
  execSync('pip list | findstr fastapi', { stdio: 'inherit' });
  execSync('pip list | findstr pymongo', { stdio: 'inherit' });
  
  console.log('Verifying frontend dependencies...');
  execSync('npm list next', { stdio: 'inherit' });
  execSync('npm list tailwindcss', { stdio: 'inherit' });
} catch (error) {
  console.warn('\n⚠️ Warning: Some dependencies might be missing.');
  console.warn('Run "pip install -r requirements.txt" and "npm install" to ensure all dependencies are installed.\n');
}

console.log('\n✅ Deployment setup completed successfully!\n');
console.log(`Environment: ${environment}`);
console.log(`App URL: ${process.env.NEXT_PUBLIC_APP_URL || config.environments.development.appUrl}`);
console.log(`Backend URL: ${process.env.NEXT_PUBLIC_BACKEND_URL || config.environments.development.backendUrl}`);
console.log('\nYou can now start the application with:');
console.log('1. Start backend: cd backend && python server.py');
console.log('2. Start frontend: npm run dev (development) or npm start (production)');