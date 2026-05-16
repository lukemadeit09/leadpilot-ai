import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#080d0c",
        panel: "#0f1614",
        line: "#22302c",
        mint: "#36d399",
        steel: "#7da4b2",
        amber: "#f6c453"
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(54,211,153,0.12), 0 22px 80px rgba(0,0,0,0.42)"
      }
    }
  },
  plugins: []
};

export default config;
