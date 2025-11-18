<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext, onMount } from 'svelte';
	import { writable, type Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	import localizedFormat from 'dayjs/plugin/localizedFormat';
	dayjs.extend(relativeTime);
	dayjs.extend(localizedFormat);

	import { getAllUserLogs, type UserLogEntry, type LogType } from '$lib/apis/user-logs';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import Modal from '$lib/components/common/Modal.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	let logs: UserLogEntry[] = [];
	let total = 0;
	let page = 1;
	let limit = 20;
	let loading = false;

	// 过滤选项
	let selectedLogType: string = 'login';  // 默认选中登录记录
	let logTypes: LogType[] = [
		{ value: 'login', label: '登录记录' },
		{ value: 'page_view', label: '页面访问' }
	];
	let selectedUserId: string = '';

	// 详情模态框
	let showDetailModal = false;
	let selectedLog: UserLogEntry | null = null;

	// 加载日志数据
	const loadLogs = async () => {
		loading = true;
		try {
			const token = localStorage.getItem('token') || '';
			const logType = selectedLogType || 'login';  // 默认使用登录记录
			const userId = selectedUserId || undefined;

			const response = await getAllUserLogs(
				token,
				page,
				limit,
				logType,
				userId,
				undefined,
				undefined
			);

			logs = response.logs;
			total = response.total;
		} catch (error: any) {
			toast.error(error || '加载日志失败');
			logs = [];
			total = 0;
		} finally {
			loading = false;
		}
	};

	// 获取日志类型标签
	const getLogTypeLabel = (type: string) => {
		const typeMap: Record<string, string> = {
			page_view: '页面访问',
			login: '登录记录'
		};
		return typeMap[type] || type;
	};

	// 获取日志类型颜色
	const getLogTypeColor = (type: string) => {
		const colorMap: Record<string, string> = {
			page_view: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
			login: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200'
		};
		return colorMap[type] || 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200';
	};

	// 打开详情模态框
	const openDetailModal = (log: UserLogEntry) => {
		selectedLog = log;
		showDetailModal = true;
	};

	// 关闭详情模态框
	const closeDetailModal = () => {
		showDetailModal = false;
		selectedLog = null;
	};

	let initialized = false;
	let lastLogType = '';
	let lastPage = 0;

	// 监听过滤条件或页码变化
	$: if (initialized && (selectedLogType !== lastLogType || page !== lastPage)) {
		if (selectedLogType !== lastLogType) {
			lastLogType = selectedLogType;
			page = 1;
			lastPage = 1;
		} else {
			lastPage = page;
		}
		loadLogs();
	}

	onMount(() => {
		lastLogType = selectedLogType;
		lastPage = page;
		initialized = true;
		loadLogs();
	});
</script>

<div class="flex flex-col w-full h-full">
	<div class="mt-0.5 mb-2 gap-1 flex flex-col md:flex-row justify-between">
		<div class="flex md:self-center text-lg font-medium px-0.5">
			{$i18n.t('用户操作日志')}

			<div class="flex self-center w-[1px] h-6 mx-2.5 bg-gray-50 dark:bg-gray-850" />

			<span class="text-lg font-medium text-gray-500 dark:text-gray-300">{total}</span>
		</div>

		<div class="flex gap-2">
			<!-- 日志类型筛选 -->
			<select
				bind:value={selectedLogType}
				class="px-5 py-1 text-sm rounded-lg bg-transparent border border-gray-300 dark:border-gray-700 outline-none"
			>
				{#each logTypes as type}
					<option value={type.value}>{type.label}</option>
				{/each}
			</select>

		</div>
	</div>

	<div class="scrollbar-hidden relative whitespace-nowrap overflow-x-auto max-w-full rounded-sm pt-0.5">
		{#if loading}
			<div class="text-center text-xs text-gray-500 dark:text-gray-400 py-8">
				{$i18n.t('加载中...')}
			</div>
		{:else if logs.length === 0}
			<div class="text-center text-xs text-gray-500 dark:text-gray-400 py-8">
				{$i18n.t('暂无日志记录')}
			</div>
		{:else}
			<table
				class="w-full text-sm text-left text-gray-500 dark:text-gray-400 table-fixed max-w-full rounded-sm"
			>
				<colgroup>
					<col style="width: 10%;" />
					<col style="width: 15%;" />
					<col style="width: 15%;" />
					<col style="width: 10%;" />
					<col style="width: 35%;" />
					<col style="width: 15%;" />
				</colgroup>
				<thead
					class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-850 dark:text-gray-400 -translate-y-0.5"
				>
					<tr>
						<th scope="col" class="px-3 py-1.5">{$i18n.t('类型')}</th>
						<th scope="col" class="px-3 py-1.5">{$i18n.t('用户名')}</th>
						<th scope="col" class="px-3 py-1.5">{$i18n.t('邮箱')}</th>
						<th scope="col" class="px-3 py-1.5">{$i18n.t('IP地址')}</th>
						<th scope="col" class="px-3 py-1.5">{$i18n.t('操作')}</th>
						<th scope="col" class="px-3 py-1.5 text-right">{$i18n.t('时间')}</th>
					</tr>
				</thead>
				<tbody>
					{#each logs as log (log.id)}
						<tr
							class="bg-white dark:bg-gray-900 dark:border-gray-850 text-xs hover:bg-gray-50 dark:hover:bg-gray-850 transition cursor-pointer"
							on:click={() => openDetailModal(log)}
							role="button"
							tabindex="0"
							on:keydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									openDetailModal(log);
								}
							}}
						>
							<td class="px-3 py-3">
								<span
									class="text-xs px-2 py-0.5 rounded {getLogTypeColor(log.type)}"
								>
									{getLogTypeLabel(log.type)}
								</span>
							</td>
							<td class="px-3 py-3 text-gray-900 dark:text-white truncate">
								{log.user_name || '-'}
							</td>
							<td class="px-3 py-3 text-gray-900 dark:text-white truncate">
								{log.user_email || '-'}
							</td>
							<td class="px-3 py-3 text-gray-900 dark:text-white truncate">
								{log.ip_address || '-'}
							</td>
							<td class="px-3 py-3 text-gray-900 dark:text-white">
								<div class="line-clamp-2 break-words">{log.action}</div>
							</td>
							<td class="px-3 py-3 text-right font-medium">
								{dayjs(log.created_at * 1000).fromNow()}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{/if}
	</div>

	{#if total > limit}
		<Pagination bind:page count={total} perPage={limit} />
	{/if}
</div>

<!-- 日志详情模态框 -->
<Modal size="md" bind:show={showDetailModal}>
	<div>
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-1">
			<div class="text-lg font-medium self-center">{$i18n.t('日志详情')}</div>
			<button class="self-center" on:click={closeDetailModal}>
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

		<div class="flex flex-col w-full px-5 pb-5 dark:text-gray-200">
			{#if selectedLog}
				<div class="space-y-4 mt-2">
					<!-- 基本信息 -->
					<div class="outline outline-1 outline-gray-200 dark:outline-gray-800 p-4 rounded-xl">
						<div class="grid grid-cols-2 gap-4 text-sm">
							<div class="flex flex-col gap-1">
								<span class="text-xs text-gray-500 dark:text-gray-500">{$i18n.t('日志类型')}</span>
								<span
									class="text-xs px-2.5 py-1 rounded-lg w-fit font-medium {getLogTypeColor(selectedLog.type)}"
								>
									{getLogTypeLabel(selectedLog.type)}
								</span>
							</div>
							<div class="flex flex-col gap-1">
								<span class="text-xs text-gray-500 dark:text-gray-500">{$i18n.t('用户名')}</span>
								<span class="text-gray-900 dark:text-gray-100 font-medium">
									{selectedLog.user_name || '-'}
								</span>
							</div>
							<div class="flex flex-col gap-1">
								<span class="text-xs text-gray-500 dark:text-gray-500">{$i18n.t('邮箱')}</span>
								<span class="text-gray-900 dark:text-gray-100 font-medium">
									{selectedLog.user_email || '-'}
								</span>
							</div>
							<div class="flex flex-col gap-1">
								<span class="text-xs text-gray-500 dark:text-gray-500">{$i18n.t('IP地址')}</span>
								<span class="text-gray-900 dark:text-gray-100 font-medium">
									{selectedLog.ip_address || '-'}
								</span>
							</div>
							<div class="flex flex-col gap-1">
								<span class="text-xs text-gray-500 dark:text-gray-500">{$i18n.t('操作时间')}</span>
								<span class="text-gray-900 dark:text-gray-100 font-medium">
									{dayjs(selectedLog.created_at * 1000).format('YYYY-MM-DD HH:mm:ss')}
								</span>
							</div>
							{#if selectedLog.user_agent}
								<div class="flex flex-col gap-1 col-span-2">
									<span class="text-xs text-gray-500 dark:text-gray-500">{$i18n.t('User Agent')}</span>
									<span class="text-gray-900 dark:text-gray-100 font-medium text-xs break-words">
										{selectedLog.user_agent}
									</span>
								</div>
							{/if}
						</div>
					</div>

					<!-- 操作描述 -->
					<div>
						<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							{$i18n.t('操作描述')}
						</div>
						<div
							class="outline outline-1 outline-gray-200 dark:outline-gray-800 p-4 rounded-xl text-sm text-gray-800 dark:text-gray-100"
						>
							{selectedLog.action}
						</div>
					</div>

					<!-- 详细信息 -->
					{#if selectedLog.details && Object.keys(selectedLog.details).length > 0}
						<div>
							<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								{$i18n.t('详细信息')}
							</div>
							<div
								class="outline outline-1 outline-gray-200 dark:outline-gray-800 p-4 rounded-xl text-sm text-gray-800 dark:text-gray-100 whitespace-pre-wrap max-h-96 overflow-y-auto scrollbar-hidden hover:scrollbar-default"
							>
								<pre class="whitespace-pre-wrap text-xs">{JSON.stringify(selectedLog.details, null, 2)}</pre>
							</div>
						</div>
					{/if}
				</div>
			{:else}
				<div class="text-center py-16 text-gray-500 dark:text-gray-500">{$i18n.t('暂无数据')}</div>
			{/if}
		</div>
	</div>
</Modal>

