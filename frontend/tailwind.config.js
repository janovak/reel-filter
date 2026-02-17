/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Content badge colors
        'content-safe': '#10b981', // green-500
        'content-warning': '#ef4444', // red-500
        'content-unavailable': '#9ca3af', // gray-400
        
        // Brand colors (can be customized)
        'brand': {
          primary: '#3b82f6', // blue-500
          secondary: '#8b5cf6', // violet-500
          accent: '#f59e0b', // amber-500
        }
      },
      screens: {
        'xs': '375px', // Minimum mobile width requirement
      },
      spacing: {
        '44': '11rem', // For 44px minimum touch targets
      }
    },
  },
  plugins: [],
}
