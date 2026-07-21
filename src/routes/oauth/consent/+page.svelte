<script>
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { getOAuthClientInfo, postOAuthConsent } from '$lib/apis/oauth';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');

	let loaded = false;
	let clientInfo = null;
	let error = null;

	let clientId = '';
	let redirectUri = '';
	let scopeStr = '';
	let stateVal = '';
	let responseType = '';

	const scopeMap = {
		openid: '身份标识',
		profile: '用户基本信息',
		email: '邮箱地址'
	};

	function parseScopes(scopes) {
		return (scopes || '').split(/\s+/).filter(Boolean).map(s => scopeMap[s.trim()] || s.trim());
	}

	onMount(async () => {
		const params = new URLSearchParams(window.location.search);
		clientId = params.get('client_id') || '';
		redirectUri = params.get('redirect_uri') || '';
		scopeStr = params.get('scope') || 'openid profile';
		stateVal = params.get('state') || '';
		responseType = params.get('response_type') || 'code';

		if (!clientId || !redirectUri) {
			error = '缺少必要参数';
			loaded = true;
			return;
		}

		const token = localStorage.getItem('token');
		if (!token) {
			// 未登录,跳转登录页,登录后回到这里
			const returnUrl = `/oauth/consent?${new URLSearchParams({
				client_id: clientId,
				redirect_uri: redirectUri,
				scope: scopeStr,
				state: stateVal,
				response_type: responseType
			}).toString()}`;
			window.location.href = `/auth?redirect=${encodeURIComponent(returnUrl)}`;
			return;
		}

		try {
			clientInfo = await getOAuthClientInfo(clientId);
		} catch (e) {
			error = '获取客户端信息失败: ' + (e?.detail || e);
		}
		loaded = true;
	});

	async function handleApprove() {
		try {
			const token = localStorage.getItem('token');
			const result = await postOAuthConsent(token, {
				client_id: clientId,
				redirect_uri: redirectUri,
				scope: scopeStr,
				state: stateVal || undefined,
				response_type: responseType
			});
			if (result?.redirect_url) {
				window.location.href = result.redirect_url;
			} else {
				toast.error('授权失败');
			}
		} catch (e) {
			toast.error('授权失败: ' + (e?.detail || e));
		}
	}

	function handleCancel() {
		const params = new URLSearchParams();
		params.set('error', 'access_denied');
		if (stateVal) params.set('state', stateVal);
		window.location.href = `${redirectUri}?${params.toString()}`;
	}

	let appName = '';
	$: {
		appName = clientInfo?.client_name || clientId || '未知应用';
	}

	let scopeList = [];
	$: {
		scopeList = parseScopes(scopeStr);
	}
</script>

<svelte:head>
	<title>{appName} - 授权登录</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 p-4">
	{#if !loaded}
		<Spinner />
	{:else if error}
		<div class="w-full max-w-md bg-white dark:bg-gray-900 rounded-2xl shadow-lg p-8 text-center">
			<div class="text-red-500 text-lg font-medium mb-2">出错了</div>
			<p class="text-gray-500 dark:text-gray-400 text-sm">{error}</p>
		</div>
	{:else}
		<div class="w-full max-w-md bg-white dark:bg-gray-900 rounded-2xl shadow-lg p-8">
			<div class="text-center mb-6">
				<div class="w-16 h-16 mx-auto mb-4 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
					<svg class="w-8 h-8 text-blue-600 dark:text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
					</svg>
				</div>
				<h1 class="text-xl font-semibold text-gray-800 dark:text-gray-100">
					授权登录
				</h1>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-2">
					<strong class="text-gray-700 dark:text-gray-200">{appName}</strong>
					请求访问你的账户信息
				</p>
			</div>

			<div class="border-t border-gray-200 dark:border-gray-700 pt-4 mb-6">
				<p class="text-sm text-gray-500 dark:text-gray-400 mb-3">该应用将获取以下权限：</p>
				<ul class="space-y-2">
					{#each scopeList as scope}
						<li class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
							<svg class="w-4 h-4 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
							</svg>
							{scope}
						</li>
					{/each}
				</ul>
			</div>

			<div class="flex gap-3">
				<button
					class="flex-1 px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 font-medium hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm"
					on:click={handleCancel}
				>
					取消
				</button>
				<button
					class="flex-1 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors text-sm"
					on:click={handleApprove}
				>
					同意授权
				</button>
			</div>
		</div>
	{/if}
</div>