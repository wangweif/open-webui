<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext } from 'svelte';
	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	import localizedFormat from 'dayjs/plugin/localizedFormat';
	dayjs.extend(relativeTime);
	dayjs.extend(localizedFormat);

	import { deleteFeedbackById } from '$lib/apis/evaluations';

import Pagination from '$lib/components/common/Pagination.svelte';
import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import Modal from '$lib/components/common/Modal.svelte';

	const i18n = getContext('i18n');

	export let feedbacks: any[] = [];

	// 过滤出type为user_feedback的反馈
	$: userFeedbacks = feedbacks.filter((f: any) => f.type === 'user_feedback');

	// 搜索功能
	let searchInput = '';
	let search = '';

	// 排序功能
	let sortKey: 'user_name' | 'user_email' | 'created_at' = 'created_at';
	let sortOrder: 'asc' | 'desc' = 'desc';

	function setSortKey(key: 'user_name' | 'user_email' | 'created_at') {
		if (sortKey === key) {
			sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
		} else {
			sortKey = key;
			sortOrder = 'desc';
		}
		page = 1; // 排序时重置到第一页
	}

	// 处理搜索，按Enter键时触发
	const handleSearch = () => {
		search = searchInput;
		page = 1; // 搜索时重置到第一页
	};

	// 获取用户名
	const getUserName = (feedback: any) => {
		return feedback?.user?.name || feedback?.data?.user?.name || '未知用户';
	};

	// 获取用户邮箱
	const getUserEmail = (feedback: any) => {
		return feedback?.user?.email || feedback?.data?.user?.email || '-';
	};

	// 过滤和排序后的反馈列表
	$: filteredFeedbacks = userFeedbacks
		.filter((f: any) => {
			if (search === '') {
				return true;
			}
			const query = search.toLowerCase();
			const name = getUserName(f).toLowerCase();
			const email = getUserEmail(f).toLowerCase();
			const comment = (f.data?.comment || '').toLowerCase();
			const actionLabel = getActionLabel(f.data?.action || 'general').toLowerCase();
			return name.includes(query) || email.includes(query) || comment.includes(query) || actionLabel.includes(query);
		})
		.sort((a: any, b: any) => {
			let aValue: any;
			let bValue: any;

			if (sortKey === 'user_name') {
				aValue = getUserName(a);
				bValue = getUserName(b);
			} else if (sortKey === 'user_email') {
				aValue = getUserEmail(a);
				bValue = getUserEmail(b);
			} else {
				// created_at
				aValue = a.created_at || 0;
				bValue = b.created_at || 0;
			}

			if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
			if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
			return 0;
		});

	let page = 1;
	$: paginatedFeedbacks = filteredFeedbacks.slice((page - 1) * 20, page * 20);

	// 反馈内容详情模态框
	let showContentModal = false;
	let selectedFeedback: any = null;

// 删除确认
let showDeleteConfirm = false;
let pendingDeleteId: string | null = null;

	const openContentModal = (feedback: any) => {
		selectedFeedback = feedback;
		showContentModal = true;
	};

	const closeContentModal = () => {
		showContentModal = false;
		selectedFeedback = null;
	};

const confirmDeleteFeedback = async () => {
	if (!pendingDeleteId) return;
	await deleteFeedbackHandler(pendingDeleteId);
	pendingDeleteId = null;
	showDeleteConfirm = false;
};

	type UserFeedback = {
		id: string;
		type: string;
		data: {
			comment: string;
			action: string;
			user?: {
				name: string;
				email: string;
			};
		};
		user: {
			name: string;
			email: string;
			profile_image_url?: string;
		};
		created_at: number;
		updated_at: number;
	};

	const deleteFeedbackHandler = async (feedbackId: string) => {
		const response = await deleteFeedbackById(localStorage.token, feedbackId).catch((err) => {
			toast.error(err);
			return null;
		});
		if (response) {
			feedbacks = feedbacks.filter((f: any) => f.id !== feedbackId);
		}
	};

	const getActionLabel = (action: string) => {
		const labels: Record<string, string> = {
			general: '通用反馈',
			bug: '错误报告',
			feature: '功能建议',
			ui: '界面',
			performance: '性能'
		};
		return labels[action] || action;
	};
</script>

<div class="mt-0.5 mb-2 gap-1 flex flex-col md:flex-row justify-between">
	<div class="flex md:self-center text-lg font-medium px-0.5">
		{$i18n.t('反馈')}

		<div class="flex self-center w-[1px] h-6 mx-2.5 bg-gray-50 dark:bg-gray-850" />

		<span class="text-lg font-medium text-gray-500 dark:text-gray-300">{filteredFeedbacks.length}</span>
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
					placeholder="搜索用户、邮箱、类型或内容"
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

<div
	class="scrollbar-hidden relative whitespace-nowrap overflow-x-auto max-w-full rounded-sm pt-0.5"
>
	{#if filteredFeedbacks.length === 0}
		<div class="text-center text-xs text-gray-500 dark:text-gray-400 py-1">
			{search ? $i18n.t('未找到匹配的反馈') : $i18n.t('暂无用户反馈')}
		</div>
	{:else}
		<table
			class="w-full text-sm text-left text-gray-500 dark:text-gray-400 table-fixed max-w-full rounded-sm"
		>
			<colgroup>
				<col style="width: 12%;" />
				<col style="width: 18%;" />
				<col style="width: 12%;" />
				<col style="width: 40%;" />
				<col style="width: 12%;" />
				<col style="width: 6%;" />
			</colgroup>
			<thead
				class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-850 dark:text-gray-400 -translate-y-0.5"
			>
				<tr class="">
					<th
						scope="col"
						class="px-3 py-1.5 cursor-pointer select-none"
						on:click={() => setSortKey('user_name')}
					>
						<div class="flex gap-1.5 items-center">
							{$i18n.t('用户名')}
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
							{$i18n.t('邮箱')}
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

					<th scope="col" class="px-3 py-1.5 cursor-pointer select-none">
						{$i18n.t('反馈类型')}
					</th>

					<th scope="col" class="px-3 py-1.5 cursor-pointer select-none">
						{$i18n.t('反馈内容')}
					</th>

					<th
						scope="col"
						class="px-3 py-1.5 text-right cursor-pointer select-none"
						on:click={() => setSortKey('created_at')}
					>
						<div class="flex gap-1.5 items-center justify-end">
							{$i18n.t('提交时间')}
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

					<th scope="col" class="px-3 py-1.5 text-right cursor-pointer select-none"> </th>
				</tr>
			</thead>
			<tbody class="">
				{#each paginatedFeedbacks as feedback (feedback.id)}
					<tr
						class="bg-white dark:bg-gray-900 dark:border-gray-850 text-xs hover:bg-gray-50 dark:hover:bg-gray-850 transition cursor-pointer"
						on:click={(e) => {
							// 如果点击的是操作菜单，不触发详情显示
							const target = e.target;
							if (target instanceof HTMLElement && !target.closest('[data-action-menu]')) {
								openContentModal(feedback);
							}
						}}
						role="button"
						tabindex="0"
						on:keydown={(e) => {
							if (e.key === 'Enter' || e.key === ' ') {
								e.preventDefault();
								openContentModal(feedback);
							}
						}}
					>
						<td class="px-3 py-3 text-gray-900 dark:text-white truncate">
							{getUserName(feedback)}
						</td>

						<td class="px-3 py-3 text-gray-900 dark:text-white truncate">
							{getUserEmail(feedback)}
						</td>

						<td class="py-3 py-3">
							<span class="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-0.5 rounded">
								{getActionLabel(feedback.data?.action || 'general')}
							</span>
							<!-- <Badge type="info" content={getActionLabel(feedback.data?.action || 'general')} /> -->
						</td>

						<td class="px-3 py-3 text-gray-900 dark:text-white">
							<div class="line-clamp-2 break-words">
								{feedback.data?.comment || '-'}
							</div>
						</td>

						<td class="px-3 py-3 text-right font-medium">
							{dayjs(feedback.created_at * 1000).fromNow()}
						</td>

						<td
							class="px-3 py-1 text-right font-semibold justify-end"
							data-action-menu
							on:click|stopPropagation
						>
							<Tooltip content="删除记录">
								<button
									class="self-center items-center w-fit text-sm px-2 py-2 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
									on:click={async () => {
										pendingDeleteId = feedback.id;
										showDeleteConfirm = true;
									}}
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										fill="none"
										viewBox="0 0 24 24"
										stroke-width="1.5"
										stroke="currentColor"
										class="w-4 h-4"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
										/>
									</svg>
								</button>
							</Tooltip>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</div>

{#if filteredFeedbacks.length > 20}
	<Pagination bind:page count={filteredFeedbacks.length} perPage={20} />
{/if}

<ConfirmDialog
	bind:show={showDeleteConfirm}
	on:confirm={confirmDeleteFeedback}
	on:cancel={() => {
		pendingDeleteId = null;
	}}
/>

<!-- 反馈内容详情模态框 -->
<Modal size="md" bind:show={showContentModal}>
	<div>
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-1">
			<div class="text-lg font-medium self-center">{$i18n.t('反馈详情')}</div>
			<button
				class="self-center"
				on:click={() => {
					closeContentModal();
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

		<div class="flex flex-col w-full px-5 pb-5 dark:text-gray-200">
			{#if selectedFeedback}
				<div class="space-y-4 mt-2">
					<!-- 用户信息 -->
					<div class="outline outline-1 outline-gray-200 dark:outline-gray-800 p-4 rounded-xl">
						<div class="grid grid-cols-2 gap-4 text-sm">
							<div class="flex flex-col gap-1">
								<span class="text-xs text-gray-500 dark:text-gray-500">{$i18n.t('用户名')}</span>
								<span class="text-gray-900 dark:text-gray-100 font-medium">
									{getUserName(selectedFeedback)}
								</span>
							</div>
							<div class="flex flex-col gap-1">
								<span class="text-xs text-gray-500 dark:text-gray-500">{$i18n.t('邮箱')}</span>
								<span class="text-gray-900 dark:text-gray-100 font-medium">
									{getUserEmail(selectedFeedback)}
								</span>
							</div>
							<div class="flex flex-col gap-1">
								<span class="text-xs text-gray-500 dark:text-gray-500">{$i18n.t('反馈类型')}</span>
								<span class="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 px-2.5 py-1 rounded-lg w-fit font-medium">
									{getActionLabel(selectedFeedback.data?.action || 'general')}
								</span>
							</div>
							<div class="flex flex-col gap-1">
								<span class="text-xs text-gray-500 dark:text-gray-500">{$i18n.t('提交时间')}</span>
								<span class="text-gray-900 dark:text-gray-100 font-medium">
									{dayjs(selectedFeedback.created_at * 1000).format('YYYY-MM-DD HH:mm:ss')}
								</span>
							</div>
						</div>
					</div>

					<!-- 反馈内容 -->
					<div>
						<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							{$i18n.t('反馈内容')}
						</div>
						<div
							class="outline outline-1 outline-gray-200 dark:outline-gray-800 p-4 rounded-xl text-sm text-gray-800 dark:text-gray-100 whitespace-pre-wrap max-h-96 overflow-y-auto scrollbar-hidden hover:scrollbar-default"
						>
							{selectedFeedback.data?.comment || '-'}
						</div>
					</div>
				</div>
			{:else}
				<div class="text-center py-16 text-gray-500 dark:text-gray-500">{$i18n.t('暂无数据')}</div>
			{/if}
		</div>
	</div>
</Modal>

