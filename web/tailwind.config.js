/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          // Backgrounds
          bg:      '#0c0e14',   // main page background
          surface: '#131920',   // cards, sidebar
          raised:  '#1a2338',   // hover/active states, elevated cards
          border:  '#1e2d40',   // dividers and borders

          // Accent colours pulled from the ogre logo
          blue:    '#1d6fa4',   // steel blue — links, active nav, highlights
          'blue-light': '#2d8fcb',
          fire:    '#d95f0e',   // fire orange — primary CTAs
          'fire-light': '#f0721a',
          green:   '#2ea862',   // orc green — success, positive states
          silver:  '#7a90a8',   // chrome silver — muted text, decorative

          // Text
          text:    '#c8d6e8',   // primary text
          muted:   '#4a5e72',   // secondary / placeholder text

          // Legacy — kept so nothing breaks
          dark:    '#0c0e14',
          gold:    '#e2b96f',   // star ratings, favourite icon
          light:   '#131920',
        },
      },
      fontFamily: {
        sans: [
          'system-ui', '-apple-system', 'BlinkMacSystemFont',
          '"Segoe UI"', 'Roboto', 'sans-serif',
        ],
      },
      boxShadow: {
        'forge': '0 4px 24px 0 rgba(0,0,0,0.5)',
        'forge-lg': '0 8px 48px 0 rgba(0,0,0,0.7)',
      },
    },
  },
  plugins: [],
}
