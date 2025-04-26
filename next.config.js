/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['localhost'],
    // Add other domains you might load images from
    unoptimized: true,
  },
  typescript: {
    // Run type checking during build
    ignoreBuildErrors: process.env.NODE_ENV === 'development',
  },
  eslint: {
    // Run ESLint during build
    ignoreDuringBuilds: process.env.NODE_ENV === 'development',
  },
  // Add any other custom configurations here
  experimental: {
    esmExternals: false,
  },
  webpack: (config) => {
    // Further custom configuration here
    return config;
  },
}

module.exports = nextConfig