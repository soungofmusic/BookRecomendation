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
        },
        turnPage: {
          '0%': { transform: 'rotateY(0deg)' },
          '25%': { transform: 'rotateY(-20deg)' },
          '50%': { transform: 'rotateY(-180deg)' },
          '75%': { transform: 'rotateY(-20deg)' },
          '100%': { transform: 'rotateY(0deg)' },
        },
        // New animations
        bookBounce: {
          '0%, 100%': { transform: 'translateY(0) rotate(-3deg)' },
          '50%': { transform: 'translateY(-20px) rotate(3deg)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeInScale: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        bookFlip: {
          '0%': { transform: 'rotateY(0deg) scale(1)' },
          '50%': { transform: 'rotateY(180deg) scale(1.1)' },
          '100%': { transform: 'rotateY(360deg) scale(1)' },
        }
      },
      animation: {
        shake: 'shake 0.82s cubic-bezier(.36,.07,.19,.97) both',
        fadeIn: 'fadeIn 0.5s ease-out forwards',
        float: 'float 3s ease-in-out infinite',
        shimmer: 'shimmer 2s infinite linear',
        shimmerButton: 'shimmerButton 8s ease-in-out infinite',
        pulseScale: 'pulseScale 2s ease-in-out infinite',
        buttonGlow: 'buttonGlow 2s ease-in-out infinite',
        turnPage: 'turnPage 1.5s ease-in-out infinite',
        bookBounce: 'bookBounce 3s ease-in-out infinite',
        slideUp: 'slideUp 0.5s ease-out forwards',
        fadeInScale: 'fadeInScale 0.5s ease-out forwards',
        bookFlip: 'bookFlip 2s ease-in-out infinite'
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('tailwind-scrollbar'),
  ],
};