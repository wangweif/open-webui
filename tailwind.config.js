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
