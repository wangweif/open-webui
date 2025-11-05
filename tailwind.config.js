import typography from '@tailwindcss/typography';
import containerQuries from '@tailwindcss/container-queries';

/** @type {import('tailwindcss').Config} */
export default {
	darkMode: 'class',
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				gray: {
					50: 'var(--color-gray-50, #f9f9f9)',
					100: 'var(--color-gray-100, #ececec)',
					200: 'var(--color-gray-200, #e3e3e3)',
					300: 'var(--color-gray-300, #cdcdcd)',
					400: 'var(--color-gray-400, #b4b4b4)',
					500: 'var(--color-gray-500, #9b9b9b)',
					600: 'var(--color-gray-600, #676767)',
					700: 'var(--color-gray-700, #4e4e4e)',
					800: 'var(--color-gray-800, #333)',
					850: 'var(--color-gray-850, #262626)',
					900: 'var(--color-gray-900, #171717)',
					950: 'var(--color-gray-950, #0d0d0d)'
				},
				primary: {
					50: 'var(--color-primary-50, #e6f7ff)',
					100: 'var(--color-primary-100, #bae7ff)',
					200: 'var(--color-primary-200, #91d5ff)',
					300: 'var(--color-primary-300, #69c0ff)',
					400: 'var(--color-primary-400, #40a9ff)',
					500: 'var(--color-primary-500, #1890ff)',
					600: 'var(--color-primary-600, #096dd9)',
					700: 'var(--color-primary-700, #0050b3)',
					800: 'var(--color-primary-800, #003a8c)',
					900: 'var(--color-primary-900, #002766)',
					950: 'var(--color-primary-950, #001529)'
				},
				yellow: {
					50:  'var(--color-yellow-50,  #fffdea)',
					100: 'var(--color-yellow-100, #fff9c4)',
					200: 'var(--color-yellow-200, #fff59d)',
					300: 'var(--color-yellow-300, #fff176)',
					400: 'var(--color-yellow-400, #ffee58)',
					500: 'var(--color-yellow-500, #ffeb3b)',
					600: 'var(--color-yellow-600, #fdd835)',
					700: 'var(--color-yellow-700, #fbc02d)',
					800: 'var(--color-yellow-800, #f9a825)',
					900: 'var(--color-yellow-900, #f57f17)',
					950: 'var(--color-yellow-950, #f57f17)'
				},  
				red: {
					50: 'var(--color-red-50, #ffe3e3)',
					100: 'var(--color-red-100, #ffcccc)',
					200: 'var(--color-red-200, #ff9999)',
					300: 'var(--color-red-300, #ff6666)',
					400: 'var(--color-red-400, #ff3333)',
					500: 'var(--color-red-500, #ff0000)',
					600: 'var(--color-red-600, #cc0000)',
					700: 'var(--color-red-700, #990000)',
					800: 'var(--color-red-800, #660000)',
					900: 'var(--color-red-900, #330000)',
					950: 'var(--color-red-950, #1a0000)'
				}
			},
			typography: {
				DEFAULT: {
					css: {
						pre: false,
						code: false,
						'pre code': false,
						'code::before': false,
						'code::after': false
					}
				}
			},
			padding: {
				'safe-bottom': 'env(safe-area-inset-bottom)'
			}
		}
	},
	plugins: [typography, containerQuries]
};
