/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.js",
    "/App.jsx",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class", 
  theme: {
    extend: {
      colors: {
        brand: {
          light: "#7dd3fc",
          DEFAULT: "#0284c7",
          dark: "#0c4a6e",
        },
      },
      fontFamily: {
        heading: ["Poppins", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};

