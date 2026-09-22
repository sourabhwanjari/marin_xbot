import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        marine: {
          950: "#060D1A", // Deepest ocean abyss
          900: "#0B1528", // Deep oceanic navy
          850: "#0F1E38", // Panel background
          800: "#15284A", // Elevated card
          700: "#1E3A68", // Card border / hover
          600: "#2B528F",
          500: "#3B71B8",
          400: "#60A5FA",
          cyan: "#00F0FF", // High-tech neon cyan accent
          glow: "#38BDF8", // Cyan-blue highlight
          teal: "#14B8A6",
          emerald: "#10B981", // Favorable PFZ
          amber: "#F59E0B",  // Caution
          rose: "#EF4444",   // Hazard / Warning
        },
      },
      backgroundImage: {
        "marine-gradient": "radial-gradient(circle at 50% 0%, #15284a 0%, #080f1d 75%, #040810 100%)",
        "card-gradient": "linear-gradient(135deg, rgba(21, 40, 74, 0.6) 0%, rgba(11, 21, 40, 0.8) 100%)",
      },
      boxShadow: {
        "marine-cyan": "0 0 20px -5px rgba(0, 240, 255, 0.25)",
        "marine-card": "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
      },
    },
  },
  plugins: [],
};
export default config;
