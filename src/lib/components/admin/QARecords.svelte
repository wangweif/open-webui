<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import { toast } from 'svelte-sonner';
	
	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	import localizedFormat from 'dayjs/plugin/localizedFormat';
	dayjs.extend(relativeTime);
	dayjs.extend(localizedFormat);

	import Pagination from '$lib/components/common/Pagination.svelte';
	import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import QARecordDetailModal from './QARecords/QARecordDetailModal.svelte';
	import { searchQARecords, type QARecord } from '$lib/apis/qa-records';
	import { removeAllDetails } from '$lib/utils';

	const i18n = getContext('i18n');

	// 从后端获取数据
	let qaRecords: QARecord[] = [];
	let totalRecords = 0;
	let searchInput = ''; // 搜索框输入值
	let search = ''; // 实际搜索关键词
	let page = 1;
	let pageSize = 20;
	let selectedRecord: QARecord | null = null;
	let showDetailModal = false;
	let loading = false;

	let sortKey = 'created_at';
	let sortOrder: 'asc' | 'desc' = 'desc';

	let isInitialized = false;
	let lastSearch = '';
	let lastPage = 1;
	let lastSortKey = 'created_at';
	let lastSortOrder: 'asc' | 'desc' = 'desc';

	function setSortKey(key: string) {
		if (sortKey === key) {
			sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
		} else {
			sortKey = key;
			sortOrder = 'desc';
		}
		// 排序时重置到第一页
		page = 1;
	}

	const removeDetail = async() => {
		qaRecords.forEach(record => {
			record.answer = removeAllDetails(record.answer);
		});
	};

	const fetchQARecords = async () => {
		if (!isInitialized) return;
		
		loading = true;
		try {
			const response = await searchQARecords(
				localStorage.token,
				search,
				page,
				pageSize,
				sortKey,
				sortOrder
			);
			qaRecords = response.records;
			await removeDetail()
			totalRecords = response.total;
			
			// 更新上次的值
			lastSearch = search;
			lastPage = page;
			lastSortKey = sortKey;
			lastSortOrder = sortOrder;
		} catch (error) {
			console.error('获取问答记录失败:', error);
			toast.error('获取问答记录失败，请稍后重试');
			qaRecords = [];
			totalRecords = 0;
		} finally {
			loading = false;
		}
	};

	// 处理搜索，按Enter键时触发
	const handleSearch = () => {
		search = searchInput;
		page = 1; // 搜索时重置到第一页
	};

	// 监听搜索变化
	$: if (isInitialized && search !== lastSearch) {
		fetchQARecords();
	}

	// 监听页码、排序变化（不包括搜索）
	$: if (isInitialized && 
		(page !== lastPage || sortKey !== lastSortKey || sortOrder !== lastSortOrder) &&
		search === lastSearch) {
		fetchQARecords();
	}

	onMount(async () => {
		if ($user?.role !== 'admin') {
			await goto('/');
		} else {
			isInitialized = true;
			await fetchQARecords();
		}
	});

	const showDetail = (record: QARecord) => {
		selectedRecord = record;
		showDetailModal = true;
	};

	const truncateText = (text: string, maxLength: number = 50): string => {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	};
</script>

<QARecordDetailModal bind:show={showDetailModal} record={selectedRecord} />

{#if loading}
	<div class="flex justify-center items-center py-12">
		<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100"></div>
	</div>
{:else}
	<div class="mt-0.5 mb-2 gap-1 flex flex-col md:flex-row justify-between">
	<div class="flex md:self-center text-lg font-medium px-0.5">
		<div class="flex-shrink-0">问答记录</div>
		<div class="flex self-center w-[1px] h-6 mx-2.5 bg-gray-50 dark:bg-gray-850" />
		<span class="text-lg font-medium text-gray-500 dark:text-gray-300">{totalRecords}</span>
	</div>

	<div class="flex gap-1">
		<div class="flex w-full space-x-2">
			<div class="flex flex-1">
				<div class="self-center ml-1 mr-3">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 20 20"
						fill="currentColor"
						class="w-4 h-4"
					>
						<path
							fill-rule="evenodd"
							d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
							clip-rule="evenodd"
						/>
					</svg>
				</div>
				<input
					class="w-full text-sm pr-4 py-1 rounded-r-xl outline-hidden bg-transparent"
					bind:value={searchInput}
					placeholder="搜索问题、回答、用户（按Enter搜索）..."
					on:keydown={(e) => {
						if (e.key === 'Enter') {
							handleSearch();
						}
					}}
				/>
			</div>
		</div>
	</div>
</div>

<div class="scrollbar-hidden relative whitespace-nowrap overflow-x-auto max-w-full rounded-sm pt-0.5">
	<table
		class="w-full text-sm text-left text-gray-500 dark:text-gray-400 table-auto max-w-full rounded-sm"
	>
		<thead
			class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-850 dark:text-gray-400 -translate-y-0.5"
		>
			<tr>
				<th
					scope="col"
					class="px-3 py-1.5 cursor-pointer select-none"
					on:click={() => setSortKey('user_name')}
				>
					<div class="flex gap-1.5 items-center">
						用户名
						{#if sortKey === 'user_name'}
							<span class="font-normal">
								{#if sortOrder === 'asc'}
									<ChevronUp className="size-2" />
								{:else}
									<ChevronDown className="size-2" />
								{/if}
							</span>
						{:else}
							<span class="invisible">
								<ChevronUp className="size-2" />
							</span>
						{/if}
					</div>
				</th>
				<th
					scope="col"
					class="px-3 py-1.5 cursor-pointer select-none"
					on:click={() => setSortKey('user_email')}
				>
					<div class="flex gap-1.5 items-center">
						邮箱
						{#if sortKey === 'user_email'}
							<span class="font-normal">
								{#if sortOrder === 'asc'}
									<ChevronUp className="size-2" />
								{:else}
									<ChevronDown className="size-2" />
								{/if}
							</span>
						{:else}
							<span class="invisible">
								<ChevronUp className="size-2" />
							</span>
						{/if}
					</div>
				</th>
				<th scope="col" class="px-3 py-1.5">
					<div class="flex gap-1.5 items-center">问题</div>
				</th>
				<th scope="col" class="px-3 py-1.5">
					<div class="flex gap-1.5 items-center">回答</div>
				</th>
				<th scope="col" class="px-3 py-1.5">
					<div class="flex gap-1.5 items-center">附件</div>
				</th>
				<th scope="col" class="px-3 py-1.5">
					<div class="flex gap-1.5 items-center">应用</div>
				</th>
				<th
					scope="col"
					class="px-3 py-1.5 cursor-pointer select-none"
					on:click={() => setSortKey('created_at')}
				>
					<div class="flex gap-1.5 items-center">
						时间
						{#if sortKey === 'created_at'}
							<span class="font-normal">
								{#if sortOrder === 'asc'}
									<ChevronUp className="size-2" />
								{:else}
									<ChevronDown className="size-2" />
								{/if}
							</span>
						{:else}
							<span class="invisible">
								<ChevronUp className="size-2" />
							</span>
						{/if}
					</div>
				</th>
				<th scope="col" class="px-3 py-1.5 text-right">操作</th>
			</tr>
		</thead>
		<tbody>
			{#each qaRecords as record}
				<tr class="bg-white dark:bg-gray-900 dark:border-gray-850 text-xs hover:bg-gray-50 dark:hover:bg-gray-850 transition">
					<td class="px-3 py-2 font-medium text-gray-900 dark:text-white">
						{record.user_name}
					</td>
					<td class="px-3 py-2">{record.user_email}</td>
					<td class="px-3 py-2 max-w-xs">
						<div class="truncate" title={record.question}>
							{truncateText(record.question, 40)}
						</div>
					</td>
					<td class="px-3 py-2 max-w-md">
						<div class="truncate" title={record.answer}>
							{truncateText(record.answer, 60)}
						</div>
					</td>
					<td class="px-3 py-2">
						{#if record.attachments && record.attachments.length > 0}
							<div class="flex items-center gap-1">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									viewBox="0 0 16 16"
									fill="currentColor"
									class="size-3"
								>
									<path
										fill-rule="evenodd"
										d="M2 4.75C2 3.784 2.784 3 3.75 3h4.836c.464 0 .909.184 1.237.513l1.414 1.414a.25.25 0 0 0 .177.073h2.836C15.216 5 16 5.784 16 6.75v5.5c0 .966-.784 1.75-1.75 1.75h-9.5A1.75 1.75 0 0 1 3 12.25v-7.5Z"
										clip-rule="evenodd"
									/>
								</svg>
								<span>{record.attachments.length}</span>
							</div>
						{:else}
							<span class="text-gray-400">-</span>
						{/if}
					</td>
					<td class="px-3 py-2">
						<span class="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-0.5 rounded">
							{record.model_name || record.model}
						</span>
					</td>
					<td class="px-3 py-2">{dayjs(record.created_at * 1000).format('YYYY-MM-DD HH:mm')}</td>
					<td class="px-3 py-2 text-right">
						<button
							class="text-sm px-3 py-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 rounded transition"
							on:click={() => showDetail(record)}
						>
							查看详情
						</button>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>

{#if qaRecords.length === 0}
		<div class="text-center py-8 text-gray-500">
			{search ? '未找到匹配的记录' : '暂无问答记录'}
		</div>
	{/if}

	<Pagination bind:page count={totalRecords} />
{/if}

