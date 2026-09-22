/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Support webpack and asset loading for Leaflet markers if needed
  webpack: (config) => {
    return config;
  },
};

export default nextConfig;
