/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["../**/templates/*.html", "../**/templates/**/*.html", "../**/templates/**/**/*.html"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Enhanced Color Palette
        gold: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B', // Primary gold
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
        },
        // Netflix-inspired Dark Theme
        korteks: {
          red: '#E50914',
          darkred: '#B81D24',
          black: '#0F0F0F',
          darkgray: '#1A1A1A',
          gray: '#262626',
          lightgray: '#404040'
        },
        // Modern Accent Colors
        accent: {
          purple: '#8B5CF6',
          blue: '#3B82F6',
          emerald: '#10B981',
          orange: '#F97316'
        }
      },
      fontFamily: {
        sans: ['Poppins', 'Inter', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'sans-serif'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
        '6xl': ['3.75rem', { lineHeight: '1' }],
        '7xl': ['4.5rem', { lineHeight: '1' }],
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'medium': '0 4px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        'hard': '0 10px 40px -10px rgba(0, 0, 0, 0.25)',
        'gold': '0 4px 14px 0 rgba(245, 158, 11, 0.25)',
        'gold-lg': '0 10px 25px -5px rgba(245, 158, 11, 0.35)',
        'red': '0 4px 14px 0 rgba(229, 9, 20, 0.25)',
        'red-lg': '0 10px 25px -5px rgba(229, 9, 20, 0.35)',
        'glow': '0 0 20px rgba(245, 158, 11, 0.4)',
        'glow-red': '0 0 20px rgba(229, 9, 20, 0.4)',
      },
      backdropBlur: {
        'xs': '2px',
        'sm': '4px',
        'md': '8px',
        'lg': '16px',
        'xl': '24px',
        '2xl': '40px',
        '3xl': '64px',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out',
        'slide-up': 'slideUp 0.6s ease-out',
        'slide-down': 'slideDown 0.6s ease-out',
        'scale-in': 'scaleIn 0.6s ease-out',
        'float': 'float 6s ease-in-out infinite',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'shimmer': 'shimmer 2s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 5px rgba(245, 158, 11, 0.4)' },
          '50%': { boxShadow: '0 0 20px rgba(245, 158, 11, 0.8)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [
    function({ addBase, theme }) {
      addBase({
        'html': { fontSize: '16px' },
        'body': { 
          fontFamily: 'Poppins, Inter, system-ui, sans-serif',
          lineHeight: '1.6',
          color: theme('colors.gray.900'),
          backgroundColor: theme('colors.white'),
          transition: 'background-color 0.3s ease, color 0.3s ease',
        },
        '.dark body': {
          color: theme('colors.gray.100'),
          backgroundColor: theme('colors.gray.900'),
        },
      })
    },
  ],
}

