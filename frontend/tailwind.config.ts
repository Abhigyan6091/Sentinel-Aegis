import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        console: {
          bg: "#080a0f",
          panel: "#11151c",
          line: "#26303d",
          text: "#f5f7fa",
          muted: "#8d99a8",
          teal: "#24d3b5",
          amber: "#f0b84b",
          red: "#ff5c6c",
          green: "#58d68d",
        },
      },
    },
  },
  plugins: [],
};

export default config;
