/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#ecfdf5",
          100: "#d1fae5",
          500: "#10b981",
          600: "#059669",
          700: "#047857"
        },
        accent: {
          50:  "#f5f3ff",
          100: "#ede9fe",
          500: "#7c3aed",
          600: "#6d28d9",
          700: "#5b21b6"
        }
      },
      borderRadius: {
        '2xl': '1rem'
      },
      boxShadow: {
        'soft': '0 1px 2px rgba(16,24,40,.06), 0 1px 3px rgba(16,24,40,.10)'
      }
    }
  },
  plugins: []
};