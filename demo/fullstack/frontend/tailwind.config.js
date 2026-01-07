/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 主色调 - 玄青色系
        primary: {
          DEFAULT: '#6366f1',
          light: '#818cf8',
          dark: '#4f46e5',
        },
        // 强调色 - 丹朱色系
        accent: {
          DEFAULT: '#f59e0b',
          light: '#fbbf24',
        },
        // 背景色
        dark: {
          primary: '#0f0f1a',
          secondary: '#1a1a2e',
          tertiary: '#252542',
          card: 'rgba(30, 30, 50, 0.6)',
        },
        // 五行颜色
        wuxing: {
          wood: '#22c55e',
          fire: '#ef4444',
          earth: '#f59e0b',
          metal: '#e2e8f0',
          water: '#3b82f6',
        }
      },
      fontFamily: {
        sans: ['Noto Sans SC', 'system-ui', 'sans-serif'],
        serif: ['Noto Serif SC', 'serif'],
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'typing': 'typing 1.4s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        typing: {
          '0%, 100%': { transform: 'translateY(0)', opacity: '0.5' },
          '50%': { transform: 'translateY(-4px)', opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}
