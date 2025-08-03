import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Optimize for Vercel deployment
  output: "standalone",

  // Environment variables validation
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // Enable experimental features for better performance
  experimental: {
    optimizeCss: true,
  },

  // Image optimization
  images: {
    domains: ["images.unsplash.com"],
    unoptimized: false,
  },
};

export default nextConfig;
