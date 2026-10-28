/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        guinda: {
          DEFAULT: "var(--color-primary)",
          dark: "var(--color-primary-dark)",
        },
        institucional: "var(--color-navy)",
        appbg: "var(--color-paper)",
      },
      fontFamily: {
        display: ["var(--font-display)"],
        body: ["var(--font-body)"],
      },
    },
  },
  plugins: [],
};
