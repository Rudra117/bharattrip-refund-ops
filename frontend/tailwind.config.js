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
        ink: {
          DEFAULT: '#0B0F14',
          panel: '#11161D',
          card: '#161C24',
          border: '#1E2630',
          hover: '#242F3D',
        },
        paper: {
          DEFAULT: '#FAF8F4',
          panel: '#FFFFFF',
          card: '#F3EFEA',
          border: '#E4DFD7',
          hover: '#EDE7DE',
        },
        amber: {
          DEFAULT: '#FFB547',
          dim: 'rgba(255, 181, 71, 0.12)',
          border: 'rgba(255, 181, 71, 0.28)',
        },
        signal: {
          red: '#FF5C5C',
          'red-dim': 'rgba(255, 92, 92, 0.12)',
          'red-border': 'rgba(255, 92, 92, 0.3)',
          green: '#3DD6A3',
          'green-dim': 'rgba(61, 214, 163, 0.12)',
          'green-border': 'rgba(61, 214, 163, 0.3)',
          blue: '#38BDF8',
          'blue-dim': 'rgba(56, 189, 248, 0.12)',
          'blue-border': 'rgba(56, 189, 248, 0.3)',
        },
        fg: {
          primary: '#E8ECF1',
          muted: '#8A94A3',
          faint: '#4B5565',
          'primary-light': '#14181F',
          'muted-light': '#5F6978',
        }
      },
      fontFamily: {
        heading: ['"Space Grotesk"', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
