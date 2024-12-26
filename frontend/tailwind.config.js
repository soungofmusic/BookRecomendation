/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      keyframes: {
        // Animation Effects
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInScale: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },

        // Book Animations
        bookBounce: {
          '0%, 100%': { transform: 'translateY(0) rotate(-3deg)' },
          '50%': { transform: 'translateY(-20px) rotate(3deg)' },
        },
        bookFlip: {
          '0%': { transform: 'rotateY(0deg) scale(1)' },
          '50%': { transform: 'rotateY(180deg) scale(1.1)' },
          '100%': { transform: 'rotateY(360deg) scale(1)' },
        },
        turnPage: {
          '0%': { transform: 'rotateY(0deg)' },
          '25%': { transform: 'rotateY(-20deg)' },
          '50%': { transform: 'rotateY(-180deg)' },
          '75%': { transform: 'rotateY(-20deg)' },
          '100%': { transform: 'rotateY(0deg)' },
        },

        // Loading & UI Effects
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' }, 
        },
        shake: {
          '0%, 100%': { transform: 'translateX(0)' },
          '10%, 30%, 50%, 70%, 90%': { transform: 'translateX(-4px)' },
          '20%, 40%, 60%, 80%': { transform: 'translateX(4px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        shimmerButton: {
          '0%': { backgroundPosition: '200% center' },
          '100%': { backgroundPosition: '-200% center' },
        },
        skeletonLoading: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' }
        },
        pulseScale: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.05)' },
        },
        buttonGlow: {
          '0%, 100%': { boxShadow: '0 0 15px 0 rgba(59, 130, 246, 0.5)' },
          '50%': { boxShadow: '0 0 30px 5px rgba(59, 130, 246, 0.7)' },
        },
      },

      // Animation Classes
      animation: {
        // Basic Animations
        fadeIn: 'fadeIn 0.5s ease-out forwards',
        fadeInScale: 'fadeInScale 0.5s ease-out forwards',
        slideUp: 'slideUp 0.5s ease-out forwards',
        float: 'float 3s ease-in-out infinite',
        shake: 'shake 0.82s cubic-bezier(.36,.07,.19,.97) both',

        // Book Animations
        bookBounce: 'bookBounce 3s ease-in-out infinite',
        bookFlip: 'bookFlip 2s ease-in-out infinite',
        turnPage: 'turnPage 1.5s ease-in-out infinite',

        // Loading & UI Effects
        shimmer: 'shimmer 2s infinite linear',
        shimmerButton: 'shimmerButton 8s ease-in-out infinite',
        skeletonLoading: 'skeletonLoading 1.5s infinite linear',
        pulseScale: 'pulseScale 2s ease-in-out infinite',
        buttonGlow: 'buttonGlow 2s ease-in-out infinite',
      },

      // Gradients
      backgroundImage: {
        'shimmer-gradient': 'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.2) 20%, rgba(255,255,255,0.5) 60%, rgba(255,255,255,0))',
        'skeleton-gradient': 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
      },

      // Sizes
      backgroundSize: {
        'skeleton': '200% 100%',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('tailwind-scrollbar'),
  ],
};