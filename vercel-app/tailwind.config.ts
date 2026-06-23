import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        space: {
          950: '#030712',
          900: '#0f172a',
          800: '#1e293b',
          700: '#334155',
        },
        horizon: {
          500: '#38bdf8',
          400: '#60a5fa',
          300: '#93c5fd',
        },
      },
    },
  },
  plugins: [],
};

export default config;
