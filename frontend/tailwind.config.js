/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        guinda: {
          DEFAULT: "#6E1E39",
          dark: "#3F0F21",
        },
        institucional: "#1F4E79",
        appbg: "#F6F5F7",
      },
      fontFamily: {
        display: ["Cambria", "Georgia", "serif"],
        body: ["Calibri", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};