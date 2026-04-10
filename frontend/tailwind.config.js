/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'off-white': '#F9FAFB',
        'dark-grey': '#374151',
        'clinical-blue': '#06B6D4',
      }
    },
  },
  plugins: [],
}
