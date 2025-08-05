import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Environment variables validation
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // Image optimization
  images: {
    domains: ["images.unsplash.com"],
    unoptimized: false,
  },

  // Ensure proper build output
  eslint: {
    ignoreDuringBuilds: false,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
