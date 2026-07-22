<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';

	import dayjs from 'dayjs';

	import { WEBUI_NAME, user } from '$lib/stores';
	import { copyToClipboard as copyToClipboardUtil } from '$lib/utils';
	import {
		getOAuthClients,
		createOAuthClient,
		updateOAuthClient,
		deleteOAuthClient,
		resetOAuthClientSecret
	} from '$lib/apis/oauth';

	import Spinner from '$lib/components/common/Spinner.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import Badge from '$lib/components/common/Badge.svelte';

	const i18n = getContext('i18n');

	let clients: any[] = [];
	let loaded = false;

	let showCreateModal = false;
	let showEditModal = false;
	let showSecretModal = false;
	let showDeleteConfirm = false;
	let showResetConfirm = false;

	let newSecret = '';
	let newClientId = '';
	let selectedClientId = '';

	let createForm = {
		client_id: '',
		client_name: '',
		redirect_uris: ''
	};

	let editForm = {
		client_id: '',
		client_name: '',
		redirect_uris: '',
		status: 'active'
	};

	let creating = false;
	let updating = false;

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
			const result = await createOAuthClient(localStorage.token, {
				...createForm,
				grant_types: 'authorization_code,refresh_token',
				scope: 'openid profile'
			});
			newSecret = result.client_secret;
			newClientId = result.client_id;
			showCreateModal = false;
			showSecretModal = true;
			resetCreateForm();
			await loadClients();
		} catch (e) {
			toast.error('创建失败: ' + ((e as any)?.detail || e));
		}
		creating = false;
	}

	function openEditModal(client: any) {
		editForm = {
			client_id: client.client_id,
			client_name: client.client_name,
			redirect_uris: client.redirect_uris,
			status: client.status ?? 'active'
		};
		showEditModal = true;
	}

	async function handleUpdate() {
		if (!editForm.client_name || !editForm.redirect_uris) {
			toast.error('请填写必填项');
			return;
		}
		updating = true;
		try {
			await updateOAuthClient(localStorage.token, editForm.client_id, {
				client_name: editForm.client_name,
				redirect_uris: editForm.redirect_uris,
				status: editForm.status
			});
			toast.success('保存成功');
			showEditModal = false;
			await loadClients();
		} catch (e) {
			toast.error('保存失败: ' + ((e as any)?.detail || e));
		}
		updating = false;
	}

	async function handleDelete() {
		try {
			await deleteOAuthClient(localStorage.token, selectedClientId);
			toast.success('删除成功');
			await loadClients();
		} catch (e) {
			toast.error('删除失败');
		}
	}

	async function handleResetSecret() {
		try {
			const result = await resetOAuthClientSecret(localStorage.token, selectedClientId);
			newSecret = result.client_secret;
			newClientId = selectedClientId;
			showSecretModal = true;
		} catch (e) {
			toast.error('重置密钥失败');
		}
	}

	function resetCreateForm() {
		createForm = {
			client_id: '',
			client_name: '',
			redirect_uris: ''
		};
	}

	async function copyToClipboard(text: string) {
		const res = await copyToClipboardUtil(text);
		if (res) {
			toast.success('已复制到剪贴板');
		} else {
			toast.error('复制失败');
		}
	}
</script>

<svelte:head>
	<title>OAuth客户端管理 | {$WEBUI_NAME}</title>
</svelte:head>

<ConfirmDialog
	bind:show={showDeleteConfirm}
	title="删除客户端"
	message={`确定删除客户端 "${selectedClientId}" 吗？该操作不可恢复。`}
	on:confirm={handleDelete}
/>

<ConfirmDialog
	bind:show={showResetConfirm}
	title="重置密钥"
	message={`确定重置 "${selectedClientId}" 的密钥吗？旧密钥将立即失效。`}
	on:confirm={handleResetSecret}
/>

{#if !loaded}
	<div class="flex items-center justify-center h-64"><Spinner /></div>
{:else}
	<div class="mt-0.5 mb-2 gap-1 flex flex-col md:flex-row justify-between">
		<div class="flex md:self-center text-lg font-medium px-0.5">
			<div class="flex-shrink-0">OAuth 客户端</div>
			<div class="flex self-center w-[1px] h-6 mx-2.5 bg-gray-50 dark:bg-gray-850" />
			<span class="text-lg font-medium text-gray-500 dark:text-gray-300">{clients.length}</span>
		</div>

		<div class="flex gap-1">
			<Tooltip content="新建客户端">
				<button
					class="p-2 rounded-xl hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 transition font-medium text-sm flex items-center space-x-1"
					on:click={() => {
						resetCreateForm();
						showCreateModal = true;
					}}
				>
					<Plus className="size-3.5" />
				</button>
			</Tooltip>
		</div>
	</div>

	<div class="scrollbar-hidden relative whitespace-nowrap overflow-x-auto max-w-full rounded-sm pt-0.5">
		<table class="w-full text-sm text-left text-gray-500 dark:text-gray-400 table-auto max-w-full rounded-sm">
			<thead
				class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-850 dark:text-gray-400 -translate-y-0.5"
			>
				<tr>
					<th scope="col" class="px-3 py-1.5">Client ID</th>
					<th scope="col" class="px-3 py-1.5">应用名称</th>
					<th scope="col" class="px-3 py-1.5 w-full">回调地址</th>
					<th scope="col" class="px-3 py-1.5">状态</th>
					<th scope="col" class="px-3 py-1.5 whitespace-nowrap">创建时间</th>
					<th scope="col" class="px-3 py-1.5 text-right">操作</th>
				</tr>
			</thead>
			<tbody>
				{#each clients as client}
					<tr
						class="bg-white dark:bg-gray-900 dark:border-gray-850 text-xs hover:bg-gray-50 dark:hover:bg-gray-850 transition"
					>
						<td class="px-3 py-3 font-mono text-gray-600 dark:text-gray-300">
							{client.client_id}
						</td>
						<td class="px-3 py-3 font-medium text-gray-900 dark:text-white">
							{client.client_name}
						</td>
						<td class="px-3 py-3 max-w-[200px]">
							<div class="truncate" title={client.redirect_uris}>
								{client.redirect_uris}
							</div>
						</td>
						<td class="px-3 py-3">
							{#if client.status === 'active'}
								<Badge type="success" content="启用" />
							{:else}
								<Badge type="error" content="禁用" />
							{/if}
						</td>
						<td class="px-3 py-3 whitespace-nowrap">
							{dayjs(client.created_at * 1000).format('YYYY-MM-DD HH:mm')}
						</td>
						<td class="px-3 py-3 text-right">
							<div class="flex justify-end gap-1">
								<button
									class="px-2 py-1 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
									on:click={() => openEditModal(client)}
								>
									编辑
								</button>
								<button
									class="px-2 py-1 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
									on:click={() => {
										selectedClientId = client.client_id;
										showResetConfirm = true;
									}}
								>
									重置密钥
								</button>
								<button
									class="px-2 py-1 rounded-lg text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 transition"
									on:click={() => {
										selectedClientId = client.client_id;
										showDeleteConfirm = true;
									}}
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

	{#if clients.length === 0}
		<div class="text-center py-8 text-gray-500">暂无注册的 OAuth 客户端</div>
	{/if}
{/if}

<!-- 新建客户端对话框 -->
<Modal size="sm" bind:show={showCreateModal} disableClickOutside>
	<div>
		<div class="flex justify-between dark:text-gray-100 px-5 pt-4 mb-1.5">
			<div class="text-lg font-medium self-center font-primary">新建 OAuth 客户端</div>
			<button
				class="self-center"
				on:click={() => {
					showCreateModal = false;
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>

		<div class="flex flex-col w-full px-5 pb-4 dark:text-gray-200">
			<form
				class="flex flex-col w-full"
				on:submit={(e) => {
					e.preventDefault();
					handleCreate();
				}}
			>
				<div class="flex flex-col w-full">
					<div class="mb-0.5 text-xs text-gray-500">Client ID <span class="text-red-500">*</span></div>
					<input
						class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden"
						type="text"
						bind:value={createForm.client_id}
						placeholder="例如: system_a"
						autocomplete="off"
						required
					/>
				</div>

				<div class="flex flex-col w-full mt-3">
					<div class="mb-0.5 text-xs text-gray-500">应用名称 <span class="text-red-500">*</span></div>
					<input
						class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden"
						type="text"
						bind:value={createForm.client_name}
						placeholder="例如: 农科小智管理后台"
						autocomplete="off"
						required
					/>
				</div>

				<div class="flex flex-col w-full mt-3">
					<div class="mb-0.5 text-xs text-gray-500">
						回调地址 <span class="text-red-500">*</span>
					</div>
					<input
						class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden"
						type="text"
						bind:value={createForm.redirect_uris}
						placeholder="多个地址用逗号分隔,例如: http://localhost:9999/callback"
						autocomplete="off"
						required
					/>
				</div>

				<div class="flex justify-end pt-4 text-sm font-medium gap-1.5">
					<button
						class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full flex flex-row space-x-1 items-center {creating
							? ' cursor-not-allowed'
							: ''}"
						type="submit"
						disabled={creating}
					>
						{creating ? '创建中...' : '创建'}

						{#if creating}
							<div class="ml-2 self-center">
								<svg
									class="w-4 h-4"
									viewBox="0 0 24 24"
									fill="currentColor"
									xmlns="http://www.w3.org/2000/svg"
									><style>
										.spinner_ajPY {
											transform-origin: center;
											animation: spinner_AtaB 0.75s infinite linear;
										}
										@keyframes spinner_AtaB {
											100% {
												transform: rotate(360deg);
											}
										}
									</style><path
										d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z"
										opacity=".25"
									/><path
										d="M10.14,1.16a11,11,0,0,0-9,8.92A1.59,1.59,0,0,0,2.46,12,1.52,1.52,0,0,0,4.11,10.7a8,8,0,0,1,6.66-6.61A1.42,1.42,0,0,0,12,2.69h0A1.57,1.57,0,0,0,10.14,1.16Z"
										class="spinner_ajPY"
									/></svg
								>
							</div>
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
</Modal>

<!-- 编辑客户端对话框 -->
<Modal size="sm" bind:show={showEditModal} disableClickOutside>
	<div>
		<div class="flex justify-between dark:text-gray-100 px-5 pt-4 mb-1.5">
			<div class="text-lg font-medium self-center font-primary">编辑 OAuth 客户端</div>
			<button
				class="self-center"
				on:click={() => {
					showEditModal = false;
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>

		<div class="flex flex-col w-full px-5 pb-4 dark:text-gray-200">
			<form
				class="flex flex-col w-full"
				on:submit={(e) => {
					e.preventDefault();
					handleUpdate();
				}}
			>
				<div class="flex flex-col w-full">
					<div class="mb-0.5 text-xs text-gray-500">Client ID</div>
					<input
						class="w-full text-sm bg-transparent text-gray-400 dark:text-gray-500 outline-hidden cursor-not-allowed font-mono"
						type="text"
						value={editForm.client_id}
						disabled
					/>
				</div>

				<div class="flex flex-col w-full mt-3">
					<div class="mb-0.5 text-xs text-gray-500">应用名称 <span class="text-red-500">*</span></div>
					<input
						class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden"
						type="text"
						bind:value={editForm.client_name}
						placeholder="例如: 农科小智管理后台"
						autocomplete="off"
						required
					/>
				</div>

				<div class="flex flex-col w-full mt-3">
					<div class="mb-0.5 text-xs text-gray-500">
						回调地址 <span class="text-red-500">*</span>
					</div>
					<input
						class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden"
						type="text"
						bind:value={editForm.redirect_uris}
						placeholder="多个地址用逗号分隔,例如: http://localhost:9999/callback"
						autocomplete="off"
						required
					/>
				</div>

				<div class="flex flex-col w-full mt-3">
					<div class="mb-0.5 text-xs text-gray-500">状态</div>
					<select
						class="w-full text-sm bg-transparent outline-hidden dark:bg-gray-900"
						bind:value={editForm.status}
					>
						<option value="active">启用</option>
						<option value="disabled">禁用</option>
					</select>
				</div>

				<div class="flex justify-end pt-4 text-sm font-medium gap-1.5">
					<button
						class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full flex flex-row space-x-1 items-center {updating
							? ' cursor-not-allowed'
							: ''}"
						type="submit"
						disabled={updating}
					>
						{updating ? '保存中...' : '保存'}

						{#if updating}
							<div class="ml-2 self-center">
								<svg
									class="w-4 h-4"
									viewBox="0 0 24 24"
									fill="currentColor"
									xmlns="http://www.w3.org/2000/svg"
									><style>
										.spinner_ajPY {
											transform-origin: center;
											animation: spinner_AtaB 0.75s infinite linear;
										}
										@keyframes spinner_AtaB {
											100% {
												transform: rotate(360deg);
											}
										}
									</style><path
										d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z"
										opacity=".25"
									/><path
										d="M10.14,1.16a11,11,0,0,0-9,8.92A1.59,1.59,0,0,0,2.46,12,1.52,1.52,0,0,0,4.11,10.7a8,8,0,0,1,6.66-6.61A1.42,1.42,0,0,0,12,2.69h0A1.57,1.57,0,0,0,10.14,1.16Z"
										class="spinner_ajPY"
									/></svg
								>
							</div>
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
</Modal>

<!-- 密钥展示对话框 -->
<Modal size="sm" bind:show={showSecretModal} disableClickOutside>
	<div>
		<div class="flex justify-between dark:text-gray-100 px-5 pt-4 mb-1.5">
			<div class="text-lg font-medium self-center font-primary">Client Secret</div>
			<button
				class="self-center"
				on:click={() => {
					showSecretModal = false;
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>

		<div class="flex flex-col w-full px-5 pb-4 dark:text-gray-200">
			<div class="text-xs text-red-500 dark:text-red-400 mb-3">
				此密钥仅显示一次，请立即复制保存！
			</div>
			<div class="flex items-center gap-2 mb-3">
				<code
					class="flex-1 px-3 py-2 rounded-xl bg-gray-50 dark:bg-gray-850 text-xs text-gray-700 dark:text-gray-300 break-all font-mono"
					>{newSecret}</code
				>
				<button
					class="px-3.5 py-2 rounded-full bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 text-sm font-medium transition flex-shrink-0"
					on:click={() => copyToClipboard(newSecret)}
				>
					复制
				</button>
			</div>
			<div class="text-xs text-gray-500 dark:text-gray-400">
				Client ID: <code class="font-mono">{newClientId}</code>
			</div>
		</div>
	</div>
</Modal>
