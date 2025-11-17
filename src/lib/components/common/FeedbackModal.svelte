<script lang="ts">
	import { getContext, createEventDispatcher } from 'svelte';
	import { fade } from 'svelte/transition';
	import Modal from './Modal.svelte';
	import { createNewFeedback } from '$lib/apis/evaluations';
	import { user } from '$lib/stores';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let show = false;

	let feedbackText = '';
	let feedbackType = 'general';
	let loading = false;
	let success = false;

	const feedbackTypes = [
		{ value: 'general', label: '通用反馈' },
		{ value: 'bug', label: '错误报告' },
		{ value: 'feature', label: '功能建议' },
		{ value: 'ui', label: '界面' },
		{ value: 'performance', label: '性能' }
	];

	const handleSubmit = async () => {
		if (!feedbackText.trim()) {
			return;
		}

		loading = true;

		try {
			const feedbackData = {
				type: 'user_feedback',
				data: {
					comment: feedbackText.trim(),
					action: feedbackType,
					user: {
						name: $user?.name || '匿名用户',
						email: $user?.email || ''
					}
				},
				meta: {
					source: 'web_app',
					user_agent: navigator.userAgent,
					url: window.location.href
				},
				snapshot: {}
			};

			await createNewFeedback(localStorage.token, feedbackData);

			success = true;
			setTimeout(() => {
				show = false;
				success = false;
				feedbackText = '';
			}, 1500);

		} catch (error) {
			console.error('提交反馈失败:', error);
		} finally {
			loading = false;
		}
	};

	const handleClose = () => {
		show = false;
		feedbackText = '';
		success = false;
		dispatch('close');
	};

	$: if (show) {
		// 重置表单状态
		feedbackText = '';
		feedbackType = 'general';
		success = false;
	}
</script>

<Modal bind:show size="md">
	{#if show}
		<div class="flex flex-col">
			<!-- 标题栏 -->
			<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-2">
				<div class="text-lg font-medium self-center">{$i18n.t('用户反馈')}</div>
				<button
					class="self-center"
					on:click={handleClose}
					aria-label="Close"
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

			{#if success}
				<div in:fade class="flex flex-col items-center justify-center p-8 text-center">
					<div class="mb-4">
						<svg
							class="w-16 h-16 text-green-500 mx-auto"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
					</div>
					<h4 class="text-lg font-medium dark:text-gray-100 mb-2">
						{$i18n.t('反馈提交成功！')}
					</h4>
					<p class="text-gray-600 dark:text-gray-400">{$i18n.t('感谢您的反馈，我们会尽快处理。')}</p>
				</div>
			{:else}
				<!-- 表单内容 -->
				<div class="px-4 pb-3 dark:text-gray-200">
					<div class="flex flex-col w-full mb-3">
						<div class="mb-1 text-xs text-gray-500">{$i18n.t('反馈类型')}</div>
						<div class="flex-1">
							<select
								bind:value={feedbackType}
								class="w-full capitalize rounded-lg text-sm bg-transparent dark:disabled:text-gray-500 outline-hidden"
							>
								{#each feedbackTypes as type}
									<option value={type.value}>{$i18n.t(type.label)}</option>
								{/each}
							</select>
						</div>
					</div>

					<div class="flex flex-col w-full">
						<div class="mb-1 text-xs text-gray-500">
							{$i18n.t('反馈内容')}
							<span class="text-red-500">*</span>
						</div>
						<div class="flex-1">
							<textarea
								bind:value={feedbackText}
								placeholder={$i18n.t('请详细描述您的问题或建议...')}
								class="w-full rounded-lg px-3 py-2 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-hidden resize-none min-h-[120px]"
								maxlength="1000"
								rows="6"
							/>
						</div>
						<div class="text-xs text-gray-500 dark:text-gray-400 mt-1 text-right">
							{feedbackText.length}/1000
						</div>
					</div>

					<!-- 按钮栏 -->
					<div class="flex justify-end pt-3 text-sm font-medium">
						<button
							on:click={handleSubmit}
							class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full flex flex-row space-x-1 items-center {!feedbackText.trim() || loading
								? ' cursor-not-allowed opacity-50'
								: ''}"
							disabled={!feedbackText.trim() || loading}
						>
							{loading ? $i18n.t('提交中...') : $i18n.t('提交反馈')}

							{#if loading}
								<div class="ml-2 self-center">
									<svg
										class="w-4 h-4"
										viewBox="0 0 24 24"
										fill="currentColor"
										xmlns="http://www.w3.org/2000/svg"
									>
										<style>
											.spinner_ajPY {
												transform-origin: center;
												animation: spinner_AtaB 0.75s infinite linear;
											}
											@keyframes spinner_AtaB {
												100% {
													transform: rotate(360deg);
												}
											}
										</style>
										<path
											d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z"
											opacity=".25"
										/>
										<path
											d="M10.14,1.16a11,11,0,0,0-9,8.92A1.59,1.59,0,0,0,2.46,12,1.52,1.52,0,0,0,4.11,10.7a8,8,0,0,1,6.66-6.61A1.42,1.42,0,0,0,12,2.69h0A1.57,1.57,0,0,0,10.14,1.16Z"
											class="spinner_ajPY"
										/>
									</svg>
								</div>
							{/if}
						</button>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</Modal>