<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast, Toaster } from 'svelte-sonner';

	import { WEBUI_NAME, user } from '$lib/stores';
	import {
		getOAuthClients,
		createOAuthClient,
		deleteOAuthClient,
		resetOAuthClientSecret
	} from '$lib/apis/oauth';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');

	let clients = [];
	let loaded = false;

	// 新建/编辑对话框
	let showCreateModal = false;
	let showSecretModal = false;
	let newSecret = '';
	let newClientId = '';

	let createForm = {
		client_id: '',
		client_name: '',
		redirect_uris: '',
		grant_types: 'authorization_code,refresh_token',
		scope: 'openid profile'
	};

	let creating = false;

	onMount(async () => {
		if ($user?.role !== 'admin') {
			await goto('/');
			return;
		}
		await loadClients();
		loaded = true;
	});

	async function loadClients() {
		try {
			clients = await getOAuthClients(localStorage.token);
		} catch (e) {
			toast.error('加载客户端列表失败');
		}
	}

	async function handleCreate() {
		if (!createForm.client_id || !createForm.client_name || !createForm.redirect_uris) {
			toast.error('请填写必填项');
			return;
		}
		creating = true;
		try {
			const result = await createOAuthClient(localStorage.token, createForm);
			newSecret = result.client_secret;
			newClientId = result.client_id;
			showCreateModal = false;
			showSecretModal = true;
			resetCreateForm();
			await loadClients();
		} catch (e) {
			toast.error('创建失败: ' + (e?.detail || e));
		}
		creating = false;
	}

	async function handleDelete(clientId) {
		if (!confirm(`确定删除客户端 "${clientId}" 吗?该操作不可恢复。`)) return;
		try {
			await deleteOAuthClient(localStorage.token, clientId);
			toast.success('删除成功');
			await loadClients();
		} catch (e) {
			toast.error('删除失败');
		}
	}

	async function handleResetSecret(clientId) {
		if (!confirm(`确定重置 "${clientId}" 的密钥吗?旧密钥将立即失效。`)) return;
		try {
			const result = await resetOAuthClientSecret(localStorage.token, clientId);
			newSecret = result.client_secret;
			newClientId = clientId;
			showSecretModal = true;
		} catch (e) {
			toast.error('重置密钥失败');
		}
	}

	function resetCreateForm() {
		createForm = {
			client_id: '',
			client_name: '',
			redirect_uris: '',
			grant_types: 'authorization_code,refresh_token',
			scope: 'openid profile'
		};
	}

	function copyToClipboard(text) {
		navigator.clipboard.writeText(text).then(() => {
			toast.success('已复制到剪贴板');
		}).catch(() => {
			toast.error('复制失败');
		});
	}
</script>

<svelte:head>
	<title>OAuth客户端管理 | {$WEBUI_NAME}</title>
</svelte:head>

{#if !loaded}
	<div class="flex items-center justify-center h-64"><Spinner /></div>
{:else}
	<div class="p-4 max-w-5xl mx-auto">
		<div class="flex items-center justify-between mb-6">
			<div>
				<h1 class="text-2xl font-semibold text-gray-800 dark:text-gray-100">OAuth 客户端管理</h1>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">管理接入统一登录的第三方应用</p>
			</div>
			<button
				class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm transition-colors"
				on:click={() => {
					resetCreateForm();
					showCreateModal = true;
				}}
			>
				新建客户端
			</button>
		</div>

		{#if clients.length === 0}
			<div class="text-center py-16 text-gray-400 dark:text-gray-500">
				暂无注册的 OAuth 客户端
			</div>
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b border-gray-200 dark:border-gray-700 text-left text-gray-500 dark:text-gray-400">
							<th class="py-3 px-3 font-medium">Client ID</th>
							<th class="py-3 px-3 font-medium">应用名称</th>
							<th class="py-3 px-3 font-medium">回调地址</th>
							<th class="py-3 px-3 font-medium">授权类型</th>
							<th class="py-3 px-3 font-medium">状态</th>
							<th class="py-3 px-3 font-medium">创建时间</th>
							<th class="py-3 px-3 font-medium">操作</th>
						</tr>
					</thead>
					<tbody>
						{#each clients as client}
							<tr class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-850">
								<td class="py-3 px-3 font-mono text-xs text-gray-600 dark:text-gray-300">
									{client.client_id}
								</td>
								<td class="py-3 px-3 text-gray-800 dark:text-gray-200">{client.client_name}</td>
								<td class="py-3 px-3 text-xs text-gray-500 dark:text-gray-400 max-w-[200px] truncate" title={client.redirect_uris}>
									{client.redirect_uris}
								</td>
								<td class="py-3 px-3 text-xs text-gray-500 dark:text-gray-400">{client.grant_types}</td>
								<td class="py-3 px-3">
									{#if client.status === 'active'}
										<span class="px-2 py-0.5 rounded-full text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300">启用</span>
									{:else}
										<span class="px-2 py-0.5 rounded-full text-xs bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300">禁用</span>
									{/if}
								</td>
								<td class="py-3 px-3 text-xs text-gray-400 dark:text-gray-500">
									{new Date(client.created_at * 1000).toLocaleDateString()}
								</td>
								<td class="py-3 px-3">
									<div class="flex gap-2">
										<button
											class="px-2 py-1 text-xs rounded-lg bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 hover:bg-yellow-100 dark:hover:bg-yellow-900/50 transition-colors"
											on:click={() => handleResetSecret(client.client_id)}
										>
											重置密钥
										</button>
										<button
											class="px-2 py-1 text-xs rounded-lg bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors"
											on:click={() => handleDelete(client.client_id)}
										>
											删除
										</button>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
{/if}

<!-- 新建客户端对话框 -->
{#if showCreateModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" on:click|self={() => showCreateModal = false}>
		<div class="bg-white dark:bg-gray-900 rounded-2xl shadow-xl p-6 w-full max-w-lg mx-4">
			<h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">新建 OAuth 客户端</h2>
			<div class="space-y-4">
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Client ID <span class="text-red-500">*</span></label>
					<input type="text" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 text-sm" bind:value={createForm.client_id} placeholder="例如: system_a" />
				</div>
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">应用名称 <span class="text-red-500">*</span></label>
					<input type="text" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 text-sm" bind:value={createForm.client_name} placeholder="例如: 农科小智管理后台" />
				</div>
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">回调地址 <span class="text-red-500">*</span></label>
					<input type="text" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 text-sm" bind:value={createForm.redirect_uris} placeholder="多个地址用逗号分隔,例如: http://localhost:9999/callback" />
				</div>
				<div class="grid grid-cols-2 gap-4">
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">授权类型</label>
						<input type="text" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 text-sm" bind:value={createForm.grant_types} />
					</div>
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Scope</label>
						<input type="text" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 text-sm" bind:value={createForm.scope} />
					</div>
				</div>
			</div>
			<div class="flex gap-3 mt-6">
				<button
					class="flex-1 px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 font-medium hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm"
					on:click={() => showCreateModal = false}
				>
					取消
				</button>
				<button
					class="flex-1 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors text-sm disabled:opacity-50"
					on:click={handleCreate}
					disabled={creating}
				>
					{creating ? '创建中...' : '创建'}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- 密钥展示对话框 -->
{#if showSecretModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" on:click|self={() => showSecretModal = false}>
		<div class="bg-white dark:bg-gray-900 rounded-2xl shadow-xl p-6 w-full max-w-lg mx-4">
			<h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">Client Secret</h2>
			<p class="text-sm text-red-500 dark:text-red-400 mb-4">此密钥仅显示一次，请立即复制保存！</p>
			<div class="flex items-center gap-2 mb-4">
				<code class="flex-1 px-3 py-2 rounded-xl bg-gray-100 dark:bg-gray-800 text-xs text-gray-700 dark:text-gray-300 break-all font-mono">{newSecret}</code>
				<button
					class="px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors flex-shrink-0"
					on:click={() => copyToClipboard(newSecret)}
				>
					复制
				</button>
			</div>
			<div class="text-xs text-gray-500 dark:text-gray-400 mb-4">
				Client ID: <code class="font-mono">{newClientId}</code>
			</div>
			<button
				class="w-full px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 font-medium hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm"
				on:click={() => showSecretModal = false}
			>
				已保存，关闭
			</button>
		</div>
	</div>
{/if}