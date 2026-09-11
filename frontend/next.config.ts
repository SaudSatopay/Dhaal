import type { NextConfig } from "next";

const stamp = new Date()
  .toLocaleString("en-GB", { timeZone: "Asia/Kolkata", hour12: false })
  .slice(0, 17); // dd/mm/yyyy, hh:mm

const nextConfig: NextConfig = {
  env: {
    // shown in the landing footer — lets us verify a phone isn't on a stale cache
    NEXT_PUBLIC_BUILD: `b·${stamp}`,
  },
};

export default nextConfig;
