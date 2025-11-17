<script lang="ts">
	import { toast } from 'svelte-sonner';
	import fileSaver from 'file-saver';
	const { saveAs } = fileSaver;

	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	dayjs.extend(relativeTime);

	import { onMount, getContext } from 'svelte';
	const i18n = getContext('i18n');

	import { deleteFeedbackById, exportAllFeedbacks, getAllFeedbacks } from '$lib/apis/evaluations';

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import ArrowDownTray from '$lib/components/icons/ArrowDownTray.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import CloudArrowUp from '$lib/components/icons/CloudArrowUp.svelte';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import FeedbackMenu from './FeedbackMenu.svelte';
	import EllipsisHorizontal from '$lib/components/icons/EllipsisHorizontal.svelte';
	import Model from '../Settings/Evaluations/Model.svelte';
	import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';

	export let feedbacks: any[] = [];

	$: model_feedbacks = feedbacks.filter((f: any) => f.type === 'rating');

	let page = 1;

	// 搜索
	let searchInput = '';
	let search = '';

	// 排序
	type SortKey = 'user_name' | 'user_email' | 'model' | 'rating' | 'updated_at';
	let sortKey: SortKey = 'updated_at';
	let sortOrder: 'asc' | 'desc' = 'desc';

	function setSortKey(key: SortKey) {
		if (sortKey === key) {
			sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
		} else {
			sortKey = key;
			sortOrder = key === 'updated_at' ? 'desc' : 'asc';
		}
		page = 1;
	}

	const handleSearch = () => {
		search = searchInput.trim();
		page = 1;
	};

	type Feedback = {
		id: string;
		data: {
			rating: number;
			model_id: string;
			sibling_model_ids: string[] | null;
			reason: string;
			comment: string;
			tags: string[];
		};
		user: {
			name: string;
			profile_image_url: string;
		email?: string;
		};
		updated_at: number;
	};

	const getUserName = (feedback: Feedback) => feedback?.user?.name || 'Unknown User';
	const getUserEmail = (feedback: Feedback) => feedback?.user?.email || '-';
	const getModelName = (feedback: Feedback) => feedback?.data?.model_id || '-';
	const getComment = (feedback: Feedback) => feedback?.data?.comment || feedback?.data?.reason || '-';
	const getRatingValue = (feedback) => {
		const rating = Number(feedback?.data?.details?.rating);
		return Number.isFinite(rating) ? rating : null;
	};

	$: filteredFeedbacks = model_feedbacks
		.filter((f: Feedback) => {
			if (!search) return true;
			const query = search.toLowerCase();
			const name = getUserName(f).toLowerCase();
			const email = getUserEmail(f).toLowerCase();
			const modelName = getModelName(f).toLowerCase();
			const comment = getComment(f).toLowerCase();
			const rating = getRatingValue(f);

			return (
				name.includes(query) ||
				email.includes(query) ||
				modelName.includes(query) ||
				comment.includes(query) ||
				(rating !== null && rating.toString().includes(query))
			);
		})
		.sort((a: Feedback, b: Feedback) => {
			const getSortValue = (feedback: Feedback) => {
				switch (sortKey) {
					case 'user_name':
						return getUserName(feedback).toLowerCase();
					case 'user_email':
						return getUserEmail(feedback).toLowerCase();
					case 'model':
						return getModelName(feedback).toLowerCase();
					case 'rating': {
						const rating = getRatingValue(feedback);
						return rating !== null ? rating : Number.NEGATIVE_INFINITY;
					}
					case 'updated_at':
					default:
						return feedback.updated_at || 0;
				}
			};

			const aValue = getSortValue(a);
			const bValue = getSortValue(b);

			if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
			if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
			return 0;
		});

	$: paginatedFeedbacks = filteredFeedbacks.slice((page - 1) * 20, page * 20);

	type ModelStats = {
		rating: number;
		won: number;
		lost: number;
	};

	//////////////////////
	//
	// CRUD operations
	//
	//////////////////////

	const deleteFeedbackHandler = async (feedbackId: string) => {
		const response = await deleteFeedbackById(localStorage.token, feedbackId).catch((err) => {
			toast.error(err);
			return null;
		});
		if (response) {
			feedbacks = feedbacks.filter((f) => f.id !== feedbackId);
		}
	};

	const shareHandler = async () => {
		toast.success($i18n.t('Redirecting you to Open WebUI Community'));

		// remove snapshot from feedbacks
		const feedbacksToShare = feedbacks.map((f) => {
			const { snapshot, user, ...rest } = f;
			return rest;
		});
		console.log(feedbacksToShare);

		const url = 'https://openwebui.com';
		const tab = await window.open(`${url}/leaderboard`, '_blank');

		// Define the event handler function
		const messageHandler = (event) => {
			if (event.origin !== url) return;
			if (event.data === 'loaded') {
				tab.postMessage(JSON.stringify(feedbacksToShare), '*');

				// Remove the event listener after handling the message
				window.removeEventListener('message', messageHandler);
			}
		};

		window.addEventListener('message', messageHandler, false);
	};

	const exportHandler = async () => {
		const _feedbacks = await exportAllFeedbacks(localStorage.token).catch((err) => {
			toast.error(err);
			return null;
		});

		if (_feedbacks) {
			let blob = new Blob([JSON.stringify(_feedbacks)], {
				type: 'application/json'
			});
			saveAs(blob, `feedback-history-export-${Date.now()}.json`);
		}
	};
</script>

<div class="mt-0.5 mb-2 gap-2 flex flex-col md:flex-row justify-between">
	<div class="flex md:self-center text-lg font-medium px-0.5">
		{$i18n.t('模型评价')}

		<div class="flex self-center w-[1px] h-6 mx-2.5 bg-gray-50 dark:bg-gray-850" />

		<span class="text-lg font-medium text-gray-500 dark:text-gray-300">{filteredFeedbacks.length}</span>
	</div>

	<div class="flex flex-col sm:flex-row gap-2 w-full md:w-auto">
		<div class="flex flex-1 min-w-[220px]">
			<div class="self-center ml-1 mr-3 text-gray-400">
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
				class="w-full text-sm pr-4 py-1 rounded-r-xl outline-hidden bg-transparent border-b border-gray-200 dark:border-gray-800 focus:border-gray-400"
				bind:value={searchInput}
				placeholder="搜索用户名、邮箱、模型名称、评价内容（Enter确认）..."
				on:keydown={(e) => {
					if (e.key === 'Enter') {
						handleSearch();
					}
				}}
			/>
		</div>

		{#if feedbacks.length > 0}
			<div class="flex justify-end">
				<Tooltip content={$i18n.t('Export')}>
					<button
						class="p-2 rounded-xl hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 transition font-medium text-sm flex items-center space-x-1"
						on:click={() => {
							exportHandler();
						}}
					>
						<ArrowDownTray className="size-3" />
					</button>
				</Tooltip>
			</div>
		{/if}
	</div>
</div>

<div
	class="scrollbar-hidden relative whitespace-nowrap overflow-x-auto max-w-full rounded-sm pt-0.5"
>
	{#if filteredFeedbacks.length === 0}
		<div class="text-center text-xs text-gray-500 dark:text-gray-400 py-1">
			{search ? $i18n.t('未找到匹配的评价') : $i18n.t('暂无模型评价')}
		</div>
	{:else}
		<table
			class="w-full text-sm text-left text-gray-500 dark:text-gray-400 table-fixed max-w-full rounded-sm"
		>
			<colgroup>
				<col style="width: 16%;" />
				<col style="width: 18%;" />
				<col style="width: 18%;" />
				<col style="width: 28%;" />
				<col style="width: 10%;" />
				<col style="width: 10%;" />
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

					<th
						scope="col"
						class="px-3 py-1.5 cursor-pointer select-none"
						on:click={() => setSortKey('model')}
					>
						<div class="flex gap-1.5 items-center">
							{$i18n.t('模型名称')}
							{#if sortKey === 'model'}
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

					<th scope="col" class="px-3 py-1.5 select-none">
						{$i18n.t('评价内容')}
					</th>

					<th
						scope="col"
						class="px-3 py-1.5 text-right cursor-pointer select-none"
						on:click={() => setSortKey('rating')}
					>
						<div class="flex gap-1.5 items-center justify-end">
							{$i18n.t('评价分')}
							{#if sortKey === 'rating'}
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
						class="px-3 py-1.5 text-right cursor-pointer select-none"
						on:click={() => setSortKey('updated_at')}
					>
						<div class="flex gap-1.5 items-center justify-end">
							{$i18n.t('更新时间')}
							{#if sortKey === 'updated_at'}
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
					<tr class="bg-white dark:bg-gray-900 dark:border-gray-850 text-xs">
						<td class="px-3 py-3 text-gray-900 dark:text-white truncate">
							{getUserName(feedback)}
						</td>

						<td class="px-3 py-3 text-gray-900 dark:text-white truncate">
							{getUserEmail(feedback)}
						</td>

						<td class="px-3 py-3 text-gray-900 dark:text-white truncate">
							<div class="flex flex-col gap-0.5">
								<span class="font-medium">{getModelName(feedback)}</span>
								{#if feedback.data?.sibling_model_ids?.length}
									<Tooltip content={feedback.data.sibling_model_ids.join(', ')}>
										<span class="text-[0.65rem] text-gray-500 dark:text-gray-400 line-clamp-1">
											{#if feedback.data.sibling_model_ids.length > 2}
												{feedback.data.sibling_model_ids.slice(0, 2).join(', ')}, {$i18n.t(
													'and {{COUNT}} more',
													{ COUNT: feedback.data.sibling_model_ids.length - 2 }
												)}
											{:else}
												{feedback.data.sibling_model_ids.join(', ')}
											{/if}
										</span>
									</Tooltip>
								{/if}
							</div>
						</td>

						<td class="px-3 py-3 text-gray-900 dark:text-white">
							<div class="line-clamp-2 break-words">{getComment(feedback)}</div>
						</td>

						<td class="px-3 py-3 text-right font-medium text-gray-900 dark:text-white">
							<div class="flex flex-col items-end gap-1">
								<div>
									{#if getRatingValue(feedback) >= 5}
										<Badge type="info" content={getRatingValue(feedback)} />
									{:else}
										<Badge type="error" content={getRatingValue(feedback)} />
									{/if}
								</div>
							</div>
						</td>

						<td class="px-3 py-3 text-right font-medium">
							{dayjs(feedback.updated_at * 1000).fromNow()}
						</td>

						<td class="px-3 py-1 text-right font-semibold">
							<FeedbackMenu
								on:delete={() => {
									deleteFeedbackHandler(feedback.id);
								}}
							>
								<button
									class="self-center w-fit text-sm p-1.5 dark:text-gray-300 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
								>
									<EllipsisHorizontal />
								</button>
							</FeedbackMenu>
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
