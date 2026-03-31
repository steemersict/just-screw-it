/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      fontFamily: {
        heading: ['"Barlow Condensed"', 'sans-serif'],
        body: ['Barlow', 'sans-serif'],
      },
      colors: {
        primary: '#7C3AED',
        'primary-light': '#A78BFA',
        cta: '#22C55E',
        'cta-hover': '#16A34A',
        dark: '#0F0F23',
        'dark-card': '#1A1A3E',
        'dark-card-hover': '#242456',
        muted: '#94A3B8',
        'accent-orange': '#F97316',
      },
    },
  },
  plugins: [],
};
