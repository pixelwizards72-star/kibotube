/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        yt: {
          red: '#FF0000',
          darkred: '#CC0000',
          hoverred: '#E60000',
          black: '#0F0F0F',
          card: '#181818',
          gray: '#F1F1F1',
          light: '#FAFAFA',
          border: '#E5E5E5'
        }
      },
      fontFamily: {
        sans: ['Inter', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
