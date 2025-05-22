import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';

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

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
	// 加载环境变量
	const env = loadEnv(mode, process.cwd(), '');

	// 根据环境变量设置不同的应用名称
	const APP_NAME = env.PUBLIC_APP_NAME || env.APP_NAME || (env.PUBLIC_BUILD_TARGET === 'bjny' || env.BUILD_TARGET === 'bjny' ? '北京市农业农村局' : '农科小智');

	console.log(`Building for: ${env.PUBLIC_BUILD_TARGET || env.BUILD_TARGET || 'default'}, APP_NAME: ${APP_NAME}`);

	return {
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
			APP_BUILD_HASH: JSON.stringify(process.env.APP_BUILD_HASH || 'dev-build'),
			APP_NAME: JSON.stringify(APP_NAME),
			BUILD_TARGET: JSON.stringify(env.PUBLIC_BUILD_TARGET || env.BUILD_TARGET || 'default')
		},
		build: {
			sourcemap: true,
			outDir: (env.PUBLIC_BUILD_TARGET || env.BUILD_TARGET) ? `build-${env.PUBLIC_BUILD_TARGET || env.BUILD_TARGET}` : 'build'
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
	};
});
