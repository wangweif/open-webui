import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

import { viteStaticCopy } from 'vite-plugin-static-copy';

// /** @type {import('vite').Plugin} */
// const viteServerConfig = {
// 	name: 'log-request-middleware',
// 	configureServer(server) {
// 		server.middlewares.use((req, res, next) => {
// 			res.setHeader('Access-Control-Allow-Origin', '*');
// 			res.setHeader('Access-Control-Allow-Methods', 'GET');
// 			res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
// 			res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
// 			next();
// 		});
// 	}
// };

export default defineConfig({
	plugins: [
		sveltekit(),
		viteStaticCopy({
			targets: [
				{
					src: 'node_modules/onnxruntime-web/dist/*.jsep.*',

					dest: 'wasm'
				}
			]
		})
	],
	define: {
		APP_VERSION: JSON.stringify(process.env.npm_package_version),
		APP_BUILD_HASH: JSON.stringify(process.env.APP_BUILD_HASH || 'dev-build')
	},
	build: {
		sourcemap: true
	},
	worker: {
		format: 'es'
	},
	server: {
        proxy: {
          '/api': {
            target: 'http://127.0.0.1:8080', // 后端地址
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, '/api')
            },
			'/openai': {
				target: 'http://127.0.0.1:8080', // 后端地址
				changeOrigin: true,
				rewrite: (path) => path.replace(/^\/openai/, '/openai')
			},
			'/ollama': {
				target: 'http://127.0.0.1:8080', // 后端地址
				changeOrigin: true,
				rewrite: (path) => path.replace(/^\/ollama/, '/ollama')
			}
        }
    }
});
