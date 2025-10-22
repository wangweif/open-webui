<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import dayjs from 'dayjs';
	import localizedFormat from 'dayjs/plugin/localizedFormat';
	dayjs.extend(localizedFormat);

	import Modal from '$lib/components/common/Modal.svelte';
	import ImagePreview from '$lib/components/common/ImagePreview.svelte';
	import FileItemModal from '$lib/components/common/FileItemModal.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	const i18n = getContext('i18n');

	interface AttachmentInfo {
		name?: string;
		type: 'file' | 'image';
		id?: string;
		url?: string;
		content?: string;
		size?: number;
		content_type?: string;
	}

	interface QARecord {
		id: string;
		question: string;
		answer: string;
		user_name: string;
		user_email: string;
		attachments: AttachmentInfo[];
		created_at: number;
		model: string;
	}

	export let show = false;
	export let record: QARecord | null = null;

	let showImagePreview = false;
	let previewImageSrc = '';
	let previewImageAlt = '';

	let showFilePreview = false;
	let previewFileItem: any = null;

	const closeModal = () => {
		show = false;
	};

	const handleAttachmentClick = (attachment: AttachmentInfo) => {
		if (attachment.type === 'image') {
			// 图片预览
			previewImageSrc = attachment.url || '';
			previewImageAlt = attachment.name || 'Image';
			showImagePreview = true;
		} else if (attachment.type === 'file' && attachment.id) {
			// 使用文件预览组件，包含文件内容
			const fileName = attachment.name || 'File';
			previewFileItem = {
				id: attachment.id,
				name: fileName,
				type: 'file',
				url: `${WEBUI_API_BASE_URL}/files/${attachment.id}`,
				meta: {
					content_type: attachment.content_type || getContentType(fileName),
					size: attachment.size
				},
				file: attachment.content ? {
					data: {
						content: attachment.content
					}
				} : undefined,
				size: attachment.size
			};
			showFilePreview = true;
		}
	};

	const getContentType = (filename: string): string => {
		const ext = filename.toLowerCase().split('.').pop();
		const contentTypes: Record<string, string> = {
			'pdf': 'application/pdf',
			'doc': 'application/msword',
			'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
			'xls': 'application/vnd.ms-excel',
			'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
			'txt': 'text/plain',
			'csv': 'text/csv',
			'json': 'application/json',
			'xml': 'application/xml',
			'html': 'text/html',
		};
		return contentTypes[ext || ''] || 'application/octet-stream';
	};
</script>

<Modal size="lg" bind:show>
	<div>
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-1">
			<div class="text-lg font-medium self-center">问答详情</div>
			<button
				class="self-center"
				on:click={() => {
					closeModal();
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
			{#if record}
				<div class="space-y-4 mt-2">
					<!-- 用户信息 -->
					<div class="outline outline-1 outline-gray-200 dark:outline-gray-800 p-4 rounded-xl">
						
						<div class="grid grid-cols-2 gap-4 text-sm">
							<div class="flex flex-col gap-1">
								<span class="text-xs text-gray-500 dark:text-gray-500">用户名</span>
								<span class="text-gray-900 dark:text-gray-100 font-medium">{record.user_name}</span>
							</div>
							<div class="flex flex-col gap-1">
								<span class="text-xs text-gray-500 dark:text-gray-500">邮箱</span>
								<span class="text-gray-900 dark:text-gray-100 font-medium">{record.user_email}</span>
							</div>
							<div class="flex flex-col gap-1">
								<span class="text-xs text-gray-500 dark:text-gray-500">提问时间</span>
								<span class="text-gray-900 dark:text-gray-100 font-medium">
									{dayjs(record.created_at * 1000).format('YYYY-MM-DD HH:mm:ss')}
								</span>
							</div>
							<div class="flex flex-col gap-1">
								<span class="text-xs text-gray-500 dark:text-gray-500">使用模型</span>
								<span class="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 px-2.5 py-1 rounded-lg w-fit font-medium">
									{record.model}
								</span>
							</div>
						</div>
					</div>

					<!-- 问题 -->
					<div>
						<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">问题</div>
						<div class="outline outline-1 outline-gray-200 dark:outline-gray-800 p-4 rounded-xl text-sm text-gray-800 dark:text-gray-100 whitespace-pre-wrap max-h-64 overflow-y-auto scrollbar-hidden hover:scrollbar-default">
							{record.question}
						</div>
					</div>

					<!-- 附件 -->
					{#if record.attachments && record.attachments.length > 0}
						<div>
							<!-- 图片附件 -->
							{#if record.attachments.some(a => a.type === 'image')}
								<div class="mb-4">
									<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
										图片 ({record.attachments.filter(a => a.type === 'image').length})
									</div>
									<div class="grid grid-cols-6 sm:grid-cols-7 md:grid-cols-8 lg:grid-cols-9 gap-2">
										{#each record.attachments.filter(a => a.type === 'image') as attachment}
											<button
												class="relative group aspect-square rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 hover:ring-2 hover:ring-blue-500 transition-all"
												on:click={() => handleAttachmentClick(attachment)}
												title="点击查看大图"
											>
												<img
													src={attachment.url}
													alt={attachment.name || 'Image'}
													class="w-full h-full object-cover"
													loading="lazy"
												/>
												<div class="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center">
													<svg
														xmlns="http://www.w3.org/2000/svg"
														viewBox="0 0 20 20"
														fill="currentColor"
														class="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity drop-shadow-lg"
													>
														<path d="M10 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z" />
														<path
															fill-rule="evenodd"
															d="M.664 10.59a1.651 1.651 0 0 1 0-1.186A10.004 10.004 0 0 1 10 3c4.257 0 7.893 2.66 9.336 6.41.147.381.146.804 0 1.186A10.004 10.004 0 0 1 10 17c-4.257 0-7.893-2.66-9.336-6.41ZM14 10a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z"
															clip-rule="evenodd"
														/>
													</svg>
												</div>
											</button>
										{/each}
									</div>
								</div>
							{/if}

							<!-- 文件附件 -->
							{#if record.attachments.some(a => a.type === 'file')}
								<div>
									<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
										文件 ({record.attachments.filter(a => a.type === 'file').length})
									</div>
									<div class="outline outline-1 outline-gray-200 dark:outline-gray-800 rounded-xl p-3 space-y-2">
										{#each record.attachments.filter(a => a.type === 'file') as attachment}
											<button
												class="w-full flex items-center gap-2 hover:bg-gray-50 dark:hover:bg-gray-850 p-2 rounded-lg transition cursor-pointer"
												on:click={() => handleAttachmentClick(attachment)}
												title="点击预览文件"
											>
												<!-- 文件图标 -->
												<svg
													xmlns="http://www.w3.org/2000/svg"
													viewBox="0 0 16 16"
													fill="currentColor"
													class="size-4 text-gray-500 dark:text-gray-400 flex-shrink-0"
												>
													<path
														fill-rule="evenodd"
														d="M2 4.75C2 3.784 2.784 3 3.75 3h4.836c.464 0 .909.184 1.237.513l1.414 1.414a.25.25 0 0 0 .177.073h2.836C15.216 5 16 5.784 16 6.75v5.5c0 .966-.784 1.75-1.75 1.75h-9.5A1.75 1.75 0 0 1 3 12.25v-7.5Z"
														clip-rule="evenodd"
													/>
												</svg>
												<span class="text-sm text-gray-800 dark:text-gray-200 line-clamp-1 text-left">
													{attachment.name || 'File'}
												</span>
												<svg
													xmlns="http://www.w3.org/2000/svg"
													viewBox="0 0 16 16"
													fill="currentColor"
													class="size-3 text-gray-400 dark:text-gray-500 flex-shrink-0 ml-auto"
												>
													<path
														fill-rule="evenodd"
														d="M4.22 11.78a.75.75 0 0 1 0-1.06L9.44 5.5H5.75a.75.75 0 0 1 0-1.5h5.5a.75.75 0 0 1 .75.75v5.5a.75.75 0 0 1-1.5 0V6.56l-5.22 5.22a.75.75 0 0 1-1.06 0Z"
														clip-rule="evenodd"
													/>
												</svg>
											</button>
										{/each}
									</div>
								</div>
							{/if}
						</div>
					{/if}

					<!-- 回答 -->
					<div>
						<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">回答</div>
						<div class="outline outline-1 outline-gray-200 dark:outline-gray-800 p-4 rounded-xl text-sm text-gray-800 dark:text-gray-100 whitespace-pre-wrap max-h-80 overflow-y-auto scrollbar-hidden hover:scrollbar-default">
							{record.answer}
						</div>
					</div>
				</div>
			{:else}
				<div class="text-center py-16 text-gray-500 dark:text-gray-500">
					暂无数据
				</div>
			{/if}
		</div>
	</div>
</Modal>

<!-- 图片预览 -->
<ImagePreview bind:show={showImagePreview} src={previewImageSrc} alt={previewImageAlt} />

<!-- 文件预览 -->
{#if previewFileItem}
	<FileItemModal bind:show={showFilePreview} item={previewFileItem} edit={false} />
{/if}
