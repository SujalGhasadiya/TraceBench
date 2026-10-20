/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#070d1e',
          900: '#0b1329',
          850: '#0f1a36',
          800: '#152449',
          700: '#1e3366',
        },
      },
    },
  },
  plugins: [],
}
