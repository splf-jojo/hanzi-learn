/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.jsx'],
  theme: {
    extend: {
      fontFamily: {
        hanzi: ['STKaiti', 'KaiTi', 'Kaiti SC', 'Noto Serif CJK SC', 'serif'],
        ui: ['Inter', 'Avenir Next', 'Segoe UI', 'sans-serif'],
      },
      boxShadow: {
        paper: '0 18px 48px rgba(24, 24, 24, 0.08)',
      },
    },
  },
  plugins: [],
};
