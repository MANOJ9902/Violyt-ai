import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    async rewrites() {
        return [
            { source: "/brand_space/:brandSlug/edit", destination: "/brand_space/edit/:brandSlug" },
            { source: "/brand_space/:brandSlug/view", destination: "/brand_space/view/:brandSlug" },
            { source: "/brand_space/:brandSlug/sharing", destination: "/brand_space/sharing/:brandSlug" },
        ];
    },
    // Allow Cloudflare quick tunnels to hit the Next.js dev server without "Unauthorized".
    allowedDevOrigins: [
        "*.trycloudflare.com",
        "storm-exams-this-plane.trycloudflare.com",
        "appreciation-ten-vii-rarely.trycloudflare.com",
    ],
    images: {
        remotePatterns: [
            {
                protocol: "http",
                hostname: "localhost",
                port: "8000",
                pathname: "/api/v1/storage/**",
            },
            {
                protocol: "http",
                hostname: "localhost",
                port: "8000",
                pathname: "/storage/**",
            },
            {
                protocol: "https",
                hostname: "*.trycloudflare.com",
                pathname: "/storage/**",
            },
            {
                protocol: "https",
                hostname: "*.trycloudflare.com",
                pathname: "/api/v1/storage/**",
            },
        ],
    },
};

export default nextConfig;
