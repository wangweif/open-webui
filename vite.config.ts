import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';
import type { Plugin } from 'vite';

import { viteStaticCopy } from 'vite-plugin-static-copy';

const stripCssCascadeLayers = (css: string) => {
	let output = '';
	let index = 0;

	while (index < css.length) {
		const layerIndex = css.indexOf('@layer', index);

		if (layerIndex === -1) {
			output += css.slice(index);
			break;
		}

		output += css.slice(index, layerIndex);

		let cursor = layerIndex + '@layer'.length;
		while (cursor < css.length && /\s/.test(css[cursor])) {
			cursor += 1;
		}

		const blockStart = css.indexOf('{', cursor);
		const statementEnd = css.indexOf(';', cursor);

		if (statementEnd !== -1 && (blockStart === -1 || statementEnd < blockStart)) {
			index = statementEnd + 1;
			continue;
		}

		if (blockStart === -1) {
			output += css.slice(layerIndex);
			break;
		}

		let depth = 1;
		let blockEnd = blockStart + 1;

		while (blockEnd < css.length && depth > 0) {
			const character = css[blockEnd];

			if (character === '{') {
				depth += 1;
			} else if (character === '}') {
				depth -= 1;
			}

			blockEnd += 1;
		}

		output += css.slice(blockStart + 1, blockEnd - 1);
		index = blockEnd;
	}

	return output;
};

const chrome78CssCompatPlugin = (): Plugin => ({
	name: 'chrome78-css-compat',
	generateBundle(_options, bundle) {
		for (const asset of Object.values(bundle)) {
			if (asset.type === 'asset' && asset.fileName.endsWith('.css') && typeof asset.source === 'string') {
				asset.source = stripCssCascadeLayers(asset.source);
			}
		}
	}
});

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
	const APP_NAME = env.PUBLIC_APP_NAME
	// const APP_NAME = '农科小智大模型';
	console.log(`Building for: ${env.PUBLIC_BUILD_TARGET || env.BUILD_TARGET || 'default'}, APP_NAME: ${APP_NAME}`);

	return {
		plugins: [
			sveltekit(),
			chrome78CssCompatPlugin(),
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
			BUILD_TARGET: JSON.stringify(env.PUBLIC_BUILD_TARGET || env.BUILD_TARGET || 'default'),
			FOOTER_TEXT: JSON.stringify(env.FOOTER_TEXT || "内容由 AI大模型生成，请仔细甄别。技术支持:北京市农林科学院"),
			FOOTER_TEXT_BJNY: JSON.stringify(env.FOOTER_TEXT_BJNY || "内容由 AI大模型生成，请仔细甄别。版权所有：北京市农业农村局 技术支持：北京市农村经济信息"),
			KNOWLEDGE_BASE_URL: JSON.stringify(env.KNOWLEDGE_BASE_URL || "http://know.baafs.net.cn/knowledge")
		},
		build: {
			target: 'chrome78',
			cssTarget: 'chrome78',
			sourcemap: true,
			outDir: (env.PUBLIC_BUILD_TARGET || env.BUILD_TARGET) ? `build-${env.PUBLIC_BUILD_TARGET || env.BUILD_TARGET}` : 'build'
		},
		worker: {
			format: 'es'
		},
		// 支持本地ws调试
		// server: {
		// 	proxy: {
		// 		'/api': {
		// 			target: 'http://127.0.0.1:8080',
		// 			changeOrigin: true,
		// 			ws: true, // 支持WebSocket
		// 			configure: (proxy) => {
		// 				proxy.on('error', (err) => {
		// 					console.log('proxy error', err);
		// 				});
		// 				proxy.on('proxyReq', (proxyReq, req) => {
		// 					console.log('Sending Request to the Target:', req.method, req.url);
		// 				});
		// 				proxy.on('proxyRes', (proxyRes, req) => {
		// 					console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
		// 				});
		// 			},
		// 		},
		// 	'/openai': {
		// 			target: 'http://127.0.0.1:8080',
		// 			changeOrigin: true,
		// 			ws: true,
		// 			configure: (proxy) => {
		// 				proxy.on('error', (err) => {
		// 					console.log('openai proxy error', err);
		// 				});
		// 			},
		// 	},
		// 	'/ollama': {
		// 			target: 'http://127.0.0.1:8080',
		// 			changeOrigin: true,
		// 			ws: true,
		// 			configure: (proxy) => {
		// 				proxy.on('error', (err) => {
		// 					console.log('ollama proxy error', err);
		// 				});
		// 			},
		// 	},
		// 	'/ws': {
		// 			target: 'http://127.0.0.1:8080',
		// 			changeOrigin: true,
		// 			ws: true, // WebSocket支持
		// 	}
		// 	}
		// }
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
