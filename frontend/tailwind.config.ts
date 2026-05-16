import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#08110f",
        panel: "#101816",
        line: "#24322e",
        mint: "#3ddc97",
        steel: "#7aa2b8",
        amber: "#f6c453"
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(61,220,151,0.16), 0 20px 70px rgba(0,0,0,0.35)"
      }
    }
  },
  plugins: []
};

export default config;
