/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      keyframes: {
        shake: {
          '0%, 100%': { transform: 'translateX(0)' },
          '10%, 30%, 50%, 70%, 90%': { transform: 'translateX(-4px)' },
          '20%, 40%, 60%, 80%': { transform: 'translateX(4px)' },
        },
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' }, 
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        shimmerButton: {
          '0%': { backgroundPosition: '200% center' },
          '100%': { backgroundPosition: '-200% center' },
        },
        pulseScale: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.05)' },
        },
        buttonGlow: {
          '0%, 100%': { boxShadow: '0 0 15px 0 rgba(59, 130, 246, 0.5)' },
          '50%': { boxShadow: '0 0 30px 5px rgba(59, 130, 246, 0.7)' },
          }
        }
      }, 
      animation: {
        shake: 'shake 0.82s cubic-bezier(.36,.07,.19,.97) both',
        fadeIn: 'fadeIn 0.5s ease-out forwards',
        float: 'float 3s ease-in-out infinite',
        shimmer: 'shimmer 2s infinite linear',
        shimmerButton: 'shimmerButton 8s ease-in-out infinite',
        pulseScale: 'pulseScale 2s ease-in-out infinite',
        buttonGlow: 'buttonGlow 2s ease-in-out infinite'
      }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('tailwind-scrollbar'),
  ],
};