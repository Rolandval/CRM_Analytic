/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          900: '#1e1b4b',
        },
        surface: {
          DEFAULT: '#ffffff',
          page:    '#F1F3F8',
          card:    '#ffffff',
          muted:   '#f8f9fc',
          border:  'rgba(0,0,0,0.07)',
        },
        sidebar: {
          bg:     '#0D0F14',
          hover:  'rgba(255,255,255,0.06)',
          active: 'rgba(99,102,241,0.18)',
          border: 'rgba(255,255,255,0.07)',
          text:   'rgba(255,255,255,0.55)',
          'text-active': '#ffffff',
        },
      },
      backgroundImage: {
        'brand-gradient':  'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)',
        'brand-gradient2': 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 50%, #3b82f6 100%)',
        'card-shine':      'linear-gradient(135deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.6) 100%)',
        'emerald-gradient':'linear-gradient(135deg, #10b981 0%, #059669 100%)',
        'violet-gradient': 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
        'amber-gradient':  'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
        'rose-gradient':   'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)',
        'sidebar-gradient':'linear-gradient(180deg, #0D0F14 0%, #111520 100%)',
      },
      borderRadius: {
        '2xl': '16px',
        '3xl': '20px',
        '4xl': '28px',
      },
      boxShadow: {
        'card':        '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'card-hover':  '0 8px 24px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.06)',
        'card-glow':   '0 0 0 1px rgba(99,102,241,0.15), 0 8px 24px rgba(99,102,241,0.08)',
        'btn-glow':    '0 4px 15px rgba(99,102,241,0.4)',
        'btn-glow-sm': '0 2px 8px rgba(99,102,241,0.35)',
        'popover':     '0 20px 60px rgba(0,0,0,0.15), 0 4px 16px rgba(0,0,0,0.08)',
        'inner-light': 'inset 0 1px 0 rgba(255,255,255,0.1)',
      },
      animation: {
        'fade-in':     'fadeIn 0.2s ease-out',
        'slide-up':    'slideUp 0.25s ease-out',
        'scale-in':    'scaleIn 0.15s ease-out',
        'shimmer':     'shimmer 1.6s ease-in-out infinite',
        'glow-pulse':  'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn:    { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp:   { from: { opacity: '0', transform: 'translateY(8px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        scaleIn:   { from: { opacity: '0', transform: 'scale(0.96)' }, to: { opacity: '1', transform: 'scale(1)' } },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(99,102,241,0)' },
          '50%':      { boxShadow: '0 0 0 6px rgba(99,102,241,0.15)' },
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
    },
  },
  plugins: [],
}
