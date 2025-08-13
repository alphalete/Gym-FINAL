/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2563EB',
          50: '#EBF2FF',
          100: '#DBE7FF',
          200: '#BAD0FF',
          300: '#8DB5FF',
          400: '#5A91FF',
          500: '#2563EB',
          600: '#1D4ED8',
          700: '#1E40AF',
          800: '#1E3A8A',
          900: '#1E3A8A',
        },
        success: {
          DEFAULT: '#16A34A',
          50: '#F0FDF4',
          500: '#16A34A',
          600: '#15803D',
        },
        warning: {
          DEFAULT: '#F59E0B',
          50: '#FFFBEB',
          500: '#F59E0B',
          600: '#D97706',
        },
        danger: {
          DEFAULT: '#DC2626',
          50: '#FEF2F2',
          500: '#DC2626',
          600: '#B91C1C',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'soft-md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}