const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Proxy /api/* to the backend so browser-side fetches are same-origin (no CORS).
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          // No embedding this in someone else's frame (clickjacking).
          { key: "X-Frame-Options", value: "DENY" },
          // Don't let a browser guess a response's type from its content.
          { key: "X-Content-Type-Options", value: "nosniff" },
          // Full URL only to our own pages; nothing sent to outlets we link to.
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          // No page here needs the camera, mic, or location.
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
