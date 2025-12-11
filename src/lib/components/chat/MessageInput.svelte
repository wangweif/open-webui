<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { v4 as uuidv4 } from 'uuid';
	import { createPicker, getAuthToken } from '$lib/utils/google-drive-picker';
	import { pickAndDownloadFile } from '$lib/utils/onedrive-file-picker';

	// 全局环境变量
	declare global {
		const BUILD_TARGET: string;
	}

	import { onMount, tick, getContext, createEventDispatcher, onDestroy } from 'svelte';
	const dispatch = createEventDispatcher();

	import {
		type Model,
		mobile,
		settings,
		showSidebar,
		models,
		config,
		showCallOverlay,
		tools,
		user as _user,
		showControls,
		TTSWorker,
		showPressToTalk
	} from '$lib/stores';

	import {
		blobToFile,
		compressImage,
		createMessagesList,
		extractCurlyBraceWords
	} from '$lib/utils';
	import { transcribeAudio } from '$lib/apis/audio';
	import { uploadFile } from '$lib/apis/files';
	import { generateAutoCompletion } from '$lib/apis';
	import { deleteFileById } from '$lib/apis/files';

	import { WEBUI_BASE_URL, WEBUI_API_BASE_URL, PASTED_TEXT_CHARACTER_LIMIT } from '$lib/constants';

	import InputMenu from './MessageInput/InputMenu.svelte';
	import VoiceRecording from './MessageInput/VoiceRecording.svelte';
	import FilesOverlay from './MessageInput/FilesOverlay.svelte';
	import Commands from './MessageInput/Commands.svelte';

	import RichTextInput from '../common/RichTextInput.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import FileItem from '../common/FileItem.svelte';
	import Image from '../common/Image.svelte';

	import XMark from '../icons/XMark.svelte';
	import Headphone from '../icons/Headphone.svelte';
	import GlobeAlt from '../icons/GlobeAlt.svelte';
	import PhotoSolid from '../icons/PhotoSolid.svelte';
	import Photo from '../icons/Photo.svelte';
	import CommandLine from '../icons/CommandLine.svelte';
	import { KokoroWorker } from '$lib/workers/KokoroWorker';
	import ToolServersModal from './ToolServersModal.svelte';
	import Wrench from '../icons/Wrench.svelte';
	import KnowledgeBaseSelector from './KnowledgeBaseSelector.svelte';

	const i18n = getContext('i18n');

	export let transparentBackground = false;

	export let onChange: Function = () => {};
	export let createMessagePair: Function;
	export let stopResponse: Function;

	export let autoScroll = false;

	export let atSelectedModel: Model | undefined = undefined;
	export let selectedModels: [''];

	let selectedModelIds = [];
	$: selectedModelIds = atSelectedModel !== undefined ? [atSelectedModel.id] : selectedModels;

	// 用于检测模型切换的变量
	let previousSelectedModelIds: string[] = [];
	
	// 当模型切换时，清空附件
	$: if (selectedModelIds && selectedModelIds.length > 0 && previousSelectedModelIds.length > 0) {
		const modelChanged = JSON.stringify(selectedModelIds) !== JSON.stringify(previousSelectedModelIds);
		if (modelChanged && files.length > 0) {
			// 删除已上传的文件
			files.forEach(async (file) => {
				if (file.type !== 'collection' && !file?.collection && file.id) {
					try {
						await deleteFileById(localStorage.token, file.id);
					} catch (e) {
						console.error('Failed to delete file:', e);
					}
				}
			});
			files = [];
		}
		previousSelectedModelIds = [...selectedModelIds];
	} else if (selectedModelIds && selectedModelIds.length > 0) {
		// 初次设置，不清空文件
		previousSelectedModelIds = [...selectedModelIds];
	}

	// 模型能力配置
	$: modelCapabilities = selectedModelIds.length > 0
		? $models.find((m) => m.id === selectedModelIds[0])?.info?.meta?.capabilities ?? {}
		: {};
	$: fileUploadLimit = selectedModelIds.length > 0
		? $models.find((m) => m.id === selectedModelIds[0])?.info?.meta?.fileUploadLimit ?? undefined
		: undefined;
	$: imageUploadLimit = selectedModelIds.length > 0
		? $models.find((m) => m.id === selectedModelIds[0])?.info?.meta?.imageUploadLimit ?? undefined
		: undefined;
	// 获取附件上传类型
	$: attachmentUploadType = selectedModelIds.length > 0
		? $models.find((m) => m.id === selectedModelIds[0])?.info?.meta?.attachmentUploadType
		: undefined;
	// 获取允许的文件类型配置
	$: allowedFileTypes = selectedModelIds.length > 0
		? $models.find((m) => m.id === selectedModelIds[0])?.info?.meta?.allowedFileTypes ?? []
		: [];
	$: allowedImageTypes = selectedModelIds.length > 0
		? $models.find((m) => m.id === selectedModelIds[0])?.info?.meta?.allowedImageTypes ?? []
		: [];
	// 获取是否必须上传附件的配置
	$: requireAttachment = selectedModelIds.length > 0
		? $models.find((m) => m.id === selectedModelIds[0])?.info?.meta?.requireAttachment ?? false
		: false;

	// 文件类型映射
	const FILE_TYPE_MAPPING = {
		'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
		'doc': ['application/msword'],
		'pdf': ['application/pdf'],
		'txt': ['text/plain'],
		'csv': ['text/csv'],
		'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
		'xls': ['application/vnd.ms-excel'],
		'pptx': ['application/vnd.openxmlformats-officedocument.presentationml.presentation'],
		'ppt': ['application/vnd.ms-powerpoint'],
		'md': ['text/markdown'],
		'html': ['text/html'],
		'xml': ['text/xml'],
		'json': ['application/json']
	};

	const IMAGE_TYPE_MAPPING = {
		'png': ['image/png'],
		'jpg': ['image/jpeg'],
		'jpeg': ['image/jpeg'],
		'gif': ['image/gif'],
		'webp': ['image/webp'],
		'avif': ['image/avif'],
		'svg': ['image/svg+xml']
	};

	// 验证文件类型是否被允许
	function isFileTypeAllowed(file: File): boolean {
		// 如果没有配置文件类型限制，则允许所有类型
		if (attachmentUploadType === 'file') {
			if (allowedFileTypes.length === 0) return true;
			
			// 检查文件扩展名
			const extension = file.name.split('.').pop()?.toLowerCase();
			if (!extension) return false;
			
			// 检查是否在允许的文件类型列表中
			return allowedFileTypes.some(type => {
				const mimeTypes = FILE_TYPE_MAPPING[type];
				return mimeTypes ? mimeTypes.includes(file.type) : false;
			});
		} else if (attachmentUploadType === 'image') {
			if (allowedImageTypes.length === 0) return true;
			
			// 检查图片类型
			return allowedImageTypes.some(type => {
				const mimeTypes = IMAGE_TYPE_MAPPING[type];
				return mimeTypes ? mimeTypes.includes(file.type) : false;
			});
		}
		
		return true;
	}

	// 按钮显示控制
	$: showWebSearchButton = modelCapabilities.webSearch ?? false;
	$: showKbWebSearchButton = modelCapabilities.kb_webSearch ?? false;
	$: showEnhancedSearchButton = modelCapabilities.enhancedSearch ?? false;
	$: showDeepResearchButton = modelCapabilities.deepResearch ?? false;
	$: showKnowledgeBaseButton = modelCapabilities.knowledgeBase ?? false;
	// 根据附件上传类型控制上传按钮显示
	$: showFileUploadButton = attachmentUploadType 
		? attachmentUploadType === 'file' : false;
	$: showImageUploadButton = attachmentUploadType 
		? attachmentUploadType === 'image' : false;

	// 保持原有的模型特定逻辑
	$: isRagFlowModel = selectedModelIds.includes('rag_flow_webapi_pipeline_cs');
	$: isAiPriceModel = selectedModelIds.includes('aiPrice');
	$: isWebSearchModel = selectedModelIds.includes('Qwen3:32B');
	$: isNongJingSanziModel = selectedModelIds.includes('NongJing-sanzi');
	$: isIdentificationModel = selectedModelIds.includes('identification_webapi_pipeline_cs');
	$: isAgriculturePriceModel = selectedModelIds.includes('data_query_analysis_pipeline');
	$: isPlantingModel = selectedModelIds.includes('chatbi_query_analasis_pipeline');
	$: isDocSummaryModel = selectedModelIds.includes('n8n_summary');
	$: isAgriPolicyModel = selectedModelIds.includes('AgriPolicy_pipline');
	$: isN8nProjectResearchModel = selectedModelIds.includes('n8n_project_research');
	$: isContractReviewModel = selectedModelIds.includes('contract_review');

	// 重置手动禁用标志，当模型改变时
	$: if (!showWebSearchButton) {
		webSearchEnabled = false;
	}

	export let history;
	export let taskIds = null;

	export let prompt = '';
	export let files = [];
	export let kb_ids: string[] = [];

	export let toolServers = [];

	export let selectedToolIds = [];

	export let imageGenerationEnabled = false;
	export let webSearchEnabled = false;
	export let codeInterpreterEnabled = false;

	$: onChange({
		prompt,
		files,
		selectedToolIds,
		imageGenerationEnabled,
		webSearchEnabled
	});

	let showTools = false;

	let loaded = false;
	let recording = false;

	let isComposing = false;

	// 自定义通知状态
	let ragFlowErrorTimeout;

	// 显示 RagFlow 模型文件类型错误通知
	const showRagFlowFileTypeError = () => {
		// 清除之前的定时器
		if (ragFlowErrorTimeout) {
			clearTimeout(ragFlowErrorTimeout);
		}

		// 创建全局通知元素
		if (typeof document !== 'undefined') {
			// 移除之前的通知（如果存在）
			const existingNotification = document.getElementById('rag-flow-error-notification');
			if (existingNotification) {
				existingNotification.remove();
			}

			// 创建新的通知元素
			const notification = document.createElement('div');
			notification.id = 'rag-flow-error-notification';
			notification.innerHTML = `
				<div style="
					position: fixed;
					top: 16px;
					left: 50%;
					transform: translateX(-50%);
					z-index: 99999;
					background-color: #ef4444;
					color: white;
					padding: 12px 24px;
					border-radius: 8px;
					box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
					display: flex;
					align-items: center;
					gap: 12px;
					max-width: 28rem;
					margin: 0 auto;
					transition: all 0.3s ease-in-out;
					pointer-events: auto;
				">
					<svg xmlns="http://www.w3.org/2000/svg" style="height: 20px; width: 20px; flex-shrink: 0;" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
					</svg>
					<span style="font-size: 14px; font-weight: 500;">此模型仅支持图像文件，请上传图片文件。</span>
					<button onclick="this.parentElement.parentElement.remove()" style="
						margin-left: auto;
						background: transparent;
						border: none;
						color: white;
						cursor: pointer;
						padding: 4px;
						border-radius: 50%;
						transition: background-color 0.2s;
						display: flex;
						align-items: center;
						justify-content: center;
					" onmouseover="this.style.backgroundColor='#dc2626'" onmouseout="this.style.backgroundColor='transparent'" title="关闭">
						<svg xmlns="http://www.w3.org/2000/svg" style="height: 16px; width: 16px;" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
						</svg>
					</button>
				</div>
			`;

			// 添加到 body
			document.body.appendChild(notification);

			// 3秒后自动移除
			setTimeout(() => {
				if (notification && notification.parentNode) {
					notification.remove();
				}
			}, 3000);
		}
	};

	let chatInputContainerElement;
	let chatInputElement;

	let filesInputElement;
	let commandsElement;

	let inputFiles;
	let dragged = false;

	let user = null;
	export let placeholder = '';
	// 移动端长按录音相关变量
	let isPressingVoice = false;
	let pressTimer: ReturnType<typeof setTimeout> | null = null;
	// showPressToTalk 已经从 $lib/stores 导入，作为全局状态使用
	// 这个字段用来暂存语音输入切换时输入框中的内容
	let promptText = '';


	let visionCapableModels = [];
	$: visionCapableModels = [...(atSelectedModel ? [atSelectedModel] : selectedModels)].filter(
		(model) => $models.find((m) => m.id === model)?.info?.meta?.capabilities?.vision ?? true
	);

	const scrollToBottom = () => {
		const element = document.getElementById('messages-container');
		element.scrollTo({
			top: element.scrollHeight,
			behavior: 'smooth'
		});
	};

	const screenCaptureHandler = async () => {
		try {
			// Request screen media
			const mediaStream = await navigator.mediaDevices.getDisplayMedia({
				video: { cursor: 'never' },
				audio: false
			});
			// Once the user selects a screen, temporarily create a video element
			const video = document.createElement('video');
			video.srcObject = mediaStream;
			// Ensure the video loads without affecting user experience or tab switching
			await video.play();
			// Set up the canvas to match the video dimensions
			const canvas = document.createElement('canvas');
			canvas.width = video.videoWidth;
			canvas.height = video.videoHeight;
			// Grab a single frame from the video stream using the canvas
			const context = canvas.getContext('2d');
			context.drawImage(video, 0, 0, canvas.width, canvas.height);
			// Stop all video tracks (stop screen sharing) after capturing the image
			mediaStream.getTracks().forEach((track) => track.stop());

			// bring back focus to this current tab, so that the user can see the screen capture
			window.focus();

			// Convert the canvas to a Base64 image URL
			const imageUrl = canvas.toDataURL('image/png');
			// Add the captured image to the files array to render it
			files = [...files, { type: 'image', url: imageUrl }];
			// Clean memory: Clear video srcObject
			video.srcObject = null;
		} catch (error) {
			// Handle any errors (e.g., user cancels screen sharing)
			console.error('Error capturing screen:', error);
		}
	};

	const uploadFileHandler = async (file, fullContext: boolean = false) => {
		if ($_user?.role !== 'admin' && !($_user?.permissions?.chat?.file_upload ?? true)) {
			toast.error($i18n.t('You do not have permission to upload files.'));
			return null;
		}

		// 检测是否为 contract_review 模型，如果是则检查知识库选择
		if (isContractReviewModel) {
			if (!kb_ids || kb_ids.length === 0) {
				toast.error('请选择一个知识库');
				return null;
			}
			if (kb_ids.length > 1) {
				toast.error('请选择唯一的一个知识库');
				return null;
			}
		}

		const tempItemId = uuidv4();
		const fileItem = {
			type: 'file',
			file: '',
			id: null,
			url: '',
			name: file.name,
			collection_name: '',
			status: 'uploading',
			size: file.size,
			error: '',
			itemId: tempItemId,
			...(fullContext ? { context: 'full' } : {})
		};

		if (fileItem.size == 0) {
			toast.error($i18n.t('You cannot upload an empty file.'));
			return null;
		}

		files = [...files, fileItem];

		if (
			($config?.file?.max_count ?? null) !== null &&
			files.length > ($config?.file?.max_count ?? 0)
		) {
			console.log('File exceeds max count limit:', {
				maxCount: $config?.file?.max_count ?? 0
			});
			// 缩减files规模
			files = files.slice(0, $config?.file?.max_count ?? 0);
			toast.warning(
				$i18n.t(`File count should not exceed {{maxCount}} 个.`, {
					maxCount: $config?.file?.max_count
				})
			);
			return;
		}

		try {
			// During the file upload, file content is automatically extracted.
			// 检测是否为 contract_review 模型，只有该模型才启用知识库上传
			const enableKbUpload = isContractReviewModel;
			const uploadedFile = await uploadFile(localStorage.token, file, kb_ids, enableKbUpload);

			if (uploadedFile) {
				console.log('File upload completed:', {
					id: uploadedFile.id,
					name: fileItem.name,
					collection: uploadedFile?.meta?.collection_name
				});

				if (uploadedFile.error) {
					console.warn('File upload warning:', uploadedFile.error);
					// toast.warning(uploadedFile.error);
					toast.warning($i18n.t(`Failed to parse file.`));
					files = files.filter((item) => item?.itemId !== tempItemId);
				}

				fileItem.status = 'uploaded';
				fileItem.file = uploadedFile;
				fileItem.id = uploadedFile.id;
				fileItem.collection_name =
					uploadedFile?.meta?.collection_name || uploadedFile?.collection_name;
				fileItem.url = `${WEBUI_API_BASE_URL}/files/${uploadedFile.id}`;

				files = files;
			} else {
				files = files.filter((item) => item?.itemId !== tempItemId);
			}
		} catch (e) {
			toast.error(`${e}`);
			files = files.filter((item) => item?.itemId !== tempItemId);
		}
	};

	// 检查文件上传限制的通用函数
	function checkUploadLimit(inputFiles) {
		const currentFiles = (files ?? []).filter((f) => f?.type !== 'image');
		const currentImages = (files ?? []).filter((f) => f?.type === 'image');
		
		// 分析要上传的文件
		const inputImages = inputFiles.filter((f) => f.type.startsWith('image/'));
		const inputNonImages = inputFiles.filter((f) => !f.type.startsWith('image/'));
		
		// 根据上传类型确定限制
		let limit, currentCount, fileType, totalInputCount;
		if (showImageUploadButton && !showFileUploadButton) {
			// 仅图片上传
			limit = imageUploadLimit ?? Infinity;
			currentCount = currentImages.length;
			totalInputCount = inputImages.length;
			fileType = '图片';
		} else {
			// 文件上传（包括图片）
			limit = fileUploadLimit ?? Infinity;
			currentCount = currentFiles.length + currentImages.length;
			totalInputCount = inputFiles.length;
			fileType = '文件';
		}
		
		const remaining = Math.max(0, limit - currentCount);

		if (remaining <= 0) {
			toast.warning(`超过${fileType}上传上限`);
			return { allowed: false, files: [] };
		}

		if (totalInputCount > remaining) {
			// 如果选择的总数超过剩余限制，需要智能选择
			let selectedFiles = [];
			
			if (showImageUploadButton && !showFileUploadButton) {
				// 仅图片模式：只选择图片
				selectedFiles = inputImages.slice(0, remaining);
			} else {
				// 文件模式：优先选择图片，然后选择其他文件
				const imageRemaining = Math.max(0, remaining - inputImages.length);
				selectedFiles = [
					...inputImages.slice(0, Math.min(inputImages.length, remaining)),
					...inputNonImages.slice(0, imageRemaining)
				];
			}
			
			toast.warning(`超过${fileType}上传上限，已限制为${remaining}个`);
			return { allowed: true, files: selectedFiles };
		}

		return { allowed: true, files: inputFiles };
	}

	const inputFilesHandler = async (inputFiles) => {
		console.log('Input files handler called with:', inputFiles);
		inputFiles.forEach((file) => {
			console.log('Processing file:', {
				name: file.name,
				type: file.type,
				size: file.size,
				extension: file.name.split('.').at(-1)
			});

			// 验证文件类型是否被允许
			if (!isFileTypeAllowed(file)) {
				const fileExtension = file.name.split('.').pop()?.toLowerCase() || '未知';
				const allowedTypes = attachmentUploadType === 'file' ? allowedFileTypes : allowedImageTypes;
				const typeDescription = attachmentUploadType === 'file' ? '文件' : '图片';
				
				if (allowedTypes.length > 0) {
					toast.error(`不支持的${typeDescription}类型：${fileExtension}。允许的类型：${allowedTypes.join(', ')}`);
				} else {
					toast.error(`当前模型不支持${typeDescription}上传`);
				}
				return;
			}

			if (
				($config?.file?.max_size ?? null) !== null &&
				file.size > ($config?.file?.max_size ?? 0) * 1024 * 1024
			) {
				console.log('File exceeds max size limit:', {
					fileSize: file.size,
					maxSize: ($config?.file?.max_size ?? 0) * 1024 * 1024
				});
				toast.warning(
					$i18n.t(`File size should not exceed {{maxSize}} MB.`, {
						maxSize: $config?.file?.max_size
					})
				);
				return;
			}

			// 检查 rag_flow_webapi_pipeline_cs 模型的文件类型限制
			if (
				isRagFlowModel &&
				!['image/gif', 'image/webp', 'image/jpeg', 'image/png', 'image/avif'].includes(file['type'])
			) {
				showRagFlowFileTypeError();
				return;
			}

			if (
				['image/gif', 'image/webp', 'image/jpeg', 'image/png', 'image/avif'].includes(file['type'])
			) {
				if (visionCapableModels.length === 0) {
					toast.error($i18n.t('Selected model(s) do not support image inputs'));
					return;
				}
				let reader = new FileReader();
				reader.onload = async (event) => {
					let imageUrl = event.target.result;

					if ($settings?.imageCompression ?? false) {
						const width = $settings?.imageCompressionSize?.width ?? null;
						const height = $settings?.imageCompressionSize?.height ?? null;

						if (width || height) {
							imageUrl = await compressImage(imageUrl, width, height);
						}
					}

					files = [
						...files,
						{
							type: 'image',
							url: `${imageUrl}`
						}
					];
				};
				reader.readAsDataURL(file);
			} else {
				uploadFileHandler(file);
			}
		});
	};

	const handleKeyDown = (event: KeyboardEvent) => {
		if (event.key === 'Escape') {
			console.log('Escape');
			dragged = false;
		}
	};

	const onDragOver = (e) => {
		e.preventDefault();

		// Check if a file is being dragged.
		if (e.dataTransfer?.types?.includes('Files')) {
			dragged = true;
		} else {
			dragged = false;
		}
	};

	const onDragLeave = () => {
		dragged = false;
	};

	const onDrop = async (e) => {
		e.preventDefault();
		console.log(e);

		if (e.dataTransfer?.files) {
			const inputFiles = Array.from(e.dataTransfer?.files);
			if (inputFiles && inputFiles.length > 0) {
				console.log(inputFiles);
				
				const result = checkUploadLimit(inputFiles);
				if (result.allowed && result.files.length > 0) {
					inputFilesHandler(result.files);
				}
			}
		}

		dragged = false;
	};

	onMount(async () => {
		loaded = true;

		window.setTimeout(() => {
			const chatInput = document.getElementById('chat-input');
			chatInput?.focus();
		}, 0);

		window.addEventListener('keydown', handleKeyDown);

		await tick();

		const dropzoneElement = document.getElementById('chat-container');

		dropzoneElement?.addEventListener('dragover', onDragOver);
		dropzoneElement?.addEventListener('drop', onDrop);
		dropzoneElement?.addEventListener('dragleave', onDragLeave);
	});

	onDestroy(() => {
		console.log('destroy');
		window.removeEventListener('keydown', handleKeyDown);

		const dropzoneElement = document.getElementById('chat-container');

		if (dropzoneElement) {
			dropzoneElement?.removeEventListener('dragover', onDragOver);
			dropzoneElement?.removeEventListener('drop', onDrop);
			dropzoneElement?.removeEventListener('dragleave', onDragLeave);
		}
	});
</script>

<FilesOverlay show={dragged} />

<ToolServersModal bind:show={showTools} {selectedToolIds} />

{#if loaded}
	<div class="w-full font-primary">
		<div class=" mx-auto inset-x-0 bg-transparent flex justify-center">
			<div
				class="flex flex-col px-3 {($settings?.widescreenMode ?? null)
					? 'max-w-full'
					: 'max-w-6xl'} w-full"
			>
				<div class="relative">
					{#if autoScroll === false && history?.currentId}
						<div
							class=" absolute -top-12 left-0 right-0 flex justify-center z-30 pointer-events-none"
						>
							<button
								class=" bg-white border border-gray-100 dark:border-none dark:bg-white/20 p-1.5 rounded-full pointer-events-auto"
								on:click={() => {
									autoScroll = true;
									scrollToBottom();
								}}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									viewBox="0 0 20 20"
									fill="currentColor"
									class="w-5 h-5"
								>
									<path
										fill-rule="evenodd"
										d="M10 3a.75.75 0 01.75.75v10.638l3.96-4.158a.75.75 0 111.08 1.04l-5.25 5.5a.75.75 0 01-1.08 0l-5.25-5.5a.75.75 0 111.08-1.04l3.96 4.158V3.75A.75.75 0 0110 3z"
										clip-rule="evenodd"
									/>
								</svg>
							</button>
						</div>
					{/if}
				</div>

				<div class="w-full relative">
					{#if atSelectedModel !== undefined || selectedToolIds.length > 0 || webSearchEnabled || ($settings?.webSearch ?? false) === 'always' || imageGenerationEnabled || codeInterpreterEnabled}
						<div
							class="px-3 pb-0.5 pt-1.5 text-left w-full flex flex-col absolute bottom-0 left-0 right-0 bg-linear-to-t from-white dark:from-gray-900 z-10"
						>
							{#if atSelectedModel !== undefined}
								<div class="flex items-center justify-between w-full">
									<div class="pl-[1px] flex items-center gap-2 text-sm dark:text-gray-500">
										<img
											crossorigin="anonymous"
											alt="model profile"
											class="size-3.5 max-w-[28px] object-cover rounded-full"
											src={$models.find((model) => model.id === atSelectedModel.id)?.info?.meta
												?.profile_image_url ??
												($i18n.language === 'dg-DG'
													? `/doge.png`
													: `${WEBUI_BASE_URL}/static/favicon.png`)}
										/>
										<div class="translate-y-[0.5px]">
											Talking to <span class=" font-medium">{atSelectedModel.name}</span>
										</div>
									</div>
									<div>
										<button
											class="flex items-center dark:text-gray-500"
											on:click={() => {
												atSelectedModel = undefined;
											}}
										>
											<XMark />
										</button>
									</div>
								</div>
							{/if}
						</div>
					{/if}

					<Commands
						bind:this={commandsElement}
						bind:prompt
						bind:files
						{fileUploadLimit}
						{imageUploadLimit}
						{showFileUploadButton}
						{showImageUploadButton}
						on:upload={(e) => {
							dispatch('upload', e.detail);
						}}
						on:select={(e) => {
							const data = e.detail;

							if (data?.type === 'model') {
								atSelectedModel = data.data;
							}

							const chatInputElement = document.getElementById('chat-input');
							chatInputElement?.focus();
						}}
					/>
				</div>
			</div>
		</div>

		<div class="{transparentBackground ? 'bg-transparent' : 'bg-white dark:bg-gray-900'} ">
			<div
				class="{($settings?.widescreenMode ?? null)
					? 'max-w-full'
					: 'max-w-6xl'} px-2.5 mx-auto inset-x-0"
			>
				<div class="">
					<input
						bind:this={filesInputElement}
						bind:files={inputFiles}
						type="file"
						hidden
						multiple
						on:change={async () => {
							if (inputFiles && inputFiles.length > 0) {
								const _inputFiles = Array.from(inputFiles);
								const result = checkUploadLimit(_inputFiles);
								if (result.allowed && result.files.length > 0) {
									inputFilesHandler(result.files);
								}
							} else {
								toast.error($i18n.t(`File not found.`));
							}

							filesInputElement.value = '';
						}}
					/>
						<form
							class="w-full flex gap-1.5"
							on:submit|preventDefault={() => {
								// 检查是否必须上传附件
								if (requireAttachment && (!files || files.length === 0)) {
									const attachmentTypeText = attachmentUploadType === 'file' ? '文件' : 
																attachmentUploadType === 'image' ? '图片' : '附件';
									toast.error(`此应用必须上传${attachmentTypeText}才能发送消息`);
									return;
								}
								
								// 检查是否为模型输入，不需要在此处替换链接，因为在显示响应时会处理
								// check if selectedModels support image input
								dispatch('submit', prompt);
							}}
						>
							<div
								class="flex-1 flex flex-col relative w-full shadow-lg rounded-3xl border border-gray-50 dark:border-gray-850 hover:border-gray-100 focus-within:border-gray-100 hover:dark:border-gray-800 focus-within:dark:border-gray-800 transition px-1 bg-white/90 dark:bg-gray-400/5 dark:text-gray-100"
								dir={$settings?.chatDirection ?? 'auto'}
							>
								{#if files.length > 0}
									<div class="mx-2 mt-2.5 -mb-1 flex items-center flex-wrap gap-2">
										{#each files as file, fileIdx}
											{#if file.type === 'image'}
												<div class=" relative group">
													<div class="relative flex items-center">
														<Image
															src={file.url}
															alt="input"
															imageClassName=" size-14 rounded-xl object-cover"
														/>
														{#if atSelectedModel ? visionCapableModels.length === 0 : selectedModels.length !== visionCapableModels.length}
															<Tooltip
																className=" absolute top-1 left-1"
																content={$i18n.t('{{ models }}', {
																	models: [
																		...(atSelectedModel ? [atSelectedModel] : selectedModels)
																	]
																		.filter((id) => !visionCapableModels.includes(id))
																		.join(', ')
																})}
															>
																<svg
																	xmlns="http://www.w3.org/2000/svg"
																	viewBox="0 0 24 24"
																	fill="currentColor"
																	class="size-4 fill-yellow-300"
																>
																	<path
																		fill-rule="evenodd"
																		d="M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003ZM12 8.25a.75.75 0 0 1 .75.75v3.75a.75.75 0 0 1-1.5 0V9a.75.75 0 0 1 .75-.75Zm0 8.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
																		clip-rule="evenodd"
																	/>
																</svg>
															</Tooltip>
														{/if}
													</div>
													<div class=" absolute -top-1 -right-1">
														<button
															class=" bg-white text-black border border-white rounded-full group-hover:visible invisible transition"
															type="button"
															on:click={() => {
																files.splice(fileIdx, 1);
																files = files;
															}}
														>
															<svg
																xmlns="http://www.w3.org/2000/svg"
																viewBox="0 0 20 20"
																fill="currentColor"
																class="size-4"
															>
																<path
																	d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
																/>
															</svg>
														</button>
													</div>
												</div>
											{:else}
												<FileItem
													item={file}
													name={file.name}
													type={file.type}
													size={file?.size}
													loading={file.status === 'uploading'}
													dismissible={true}
													edit={true}
													on:dismiss={async () => {
														if (file.type !== 'collection' && !file?.collection) {
															if (file.id) {
																// This will handle both file deletion and Chroma cleanup
																await deleteFileById(localStorage.token, file.id);
															}
														}

														// Remove from UI state
														files.splice(fileIdx, 1);
														files = files;
													}}
													on:click={() => {
														console.log(file);
													}}
												/>
											{/if}
										{/each}
									</div>
								{/if}

								{#if recording || $showPressToTalk}
									<div class="px-2.5 pt-2.5">
										<VoiceRecording
											bind:recording
											showPressToTalk={$showPressToTalk}
											bind:isPressingVoice
											className="p-2.5 w-full max-w-full"
											on:cancel={async () => {
												recording = false;
												$showPressToTalk = false;

												await tick();
												document.getElementById('chat-input')?.focus();
											}}
											on:confirm={async (e) => {
												console.log("confirmed");
												const { text, filename } = e.detail;
												
												// 检查是否有有效的文本内容
												if (!text || !text.trim()) {
													recording = false;
													await tick();
													document.getElementById('chat-input')?.focus();
													return;
												}
												
												prompt = `${prompt}${text} `;
												recording = false;

												await tick();
												document.getElementById('chat-input')?.focus();
												
												if($mobile){
													// 如果正在回答，则暂停回答
													if(history?.currentId && history.messages[history.currentId]?.done != true){
														await stopResponse();
													}
													await tick();
													dispatch('submit', prompt);
												}

												if ($settings?.speechAutoSend ?? false) {
													dispatch('submit', prompt);
												}
											}}
										/>
									</div>
								{:else}
									<div class="px-2.5">
										{#if $settings?.richTextInput ?? true}
										<div
											class="scrollbar-hidden text-left bg-transparent dark:text-gray-100 outline-hidden w-full pt-3 px-1 resize-none h-fit max-h-80 overflow-auto"
											id="chat-input-container"
										>
											<RichTextInput
												bind:this={chatInputElement}
												bind:value={prompt}
												id="chat-input"
												messageInput={true}
												shiftEnter={!($settings?.ctrlEnterToSend ?? false) &&
													(!$mobile ||
														!(
															'ontouchstart' in window ||
															navigator.maxTouchPoints > 0 ||
															navigator.msMaxTouchPoints > 0
														))}
												placeholder={placeholder ? placeholder : $i18n.t('Send a Message')}
												largeTextAsFile={$settings?.largeTextAsFile ?? false}
												autocomplete={$config?.features?.enable_autocomplete_generation &&
													($settings?.promptAutocomplete ?? false)}
												generateAutoCompletion={async (text) => {
													if (selectedModelIds.length === 0 || !selectedModelIds.at(0)) {
														toast.error($i18n.t('Please select a model first.'));
													}

													const res = await generateAutoCompletion(
														localStorage.token,
														selectedModelIds.at(0),
														text,
														history?.currentId
															? createMessagesList(history, history.currentId)
															: null
													).catch((error) => {
														console.log(error);

														return null;
													});

													console.log(res);
													return res;
												}}
												oncompositionstart={() => (isComposing = true)}
												oncompositionend={() => (isComposing = false)}
												on:keydown={async (e) => {
													e = e.detail.event;

													const isCtrlPressed = e.ctrlKey || e.metaKey; // metaKey is for Cmd key on Mac
													const commandsContainerElement =
														document.getElementById('commands-container');

													if (e.key === 'Escape') {
														stopResponse();
													}

													// Command/Ctrl + Shift + Enter to submit a message pair
													if (isCtrlPressed && e.key === 'Enter' && e.shiftKey) {
														e.preventDefault();
														createMessagePair(prompt);
													}

													// Check if Ctrl + R is pressed
													if (prompt === '' && isCtrlPressed && e.key.toLowerCase() === 'r') {
														e.preventDefault();
														console.log('regenerate');

														const regenerateButton = [
															...document.getElementsByClassName('regenerate-response-button')
														]?.at(-1);

														regenerateButton?.click();
													}

													if (prompt === '' && e.key == 'ArrowUp') {
														e.preventDefault();

														const userMessageElement = [
															...document.getElementsByClassName('user-message')
														]?.at(-1);

														if (userMessageElement) {
															userMessageElement.scrollIntoView({ block: 'center' });
															const editButton = [
																...document.getElementsByClassName('edit-user-message-button')
															]?.at(-1);

															editButton?.click();
														}
													}

													if (commandsContainerElement) {
														if (commandsContainerElement && e.key === 'ArrowUp') {
															e.preventDefault();
															commandsElement.selectUp();

															const commandOptionButton = [
																...document.getElementsByClassName('selected-command-option-button')
															]?.at(-1);
															commandOptionButton.scrollIntoView({ block: 'center' });
														}

														if (commandsContainerElement && e.key === 'ArrowDown') {
															e.preventDefault();
															commandsElement.selectDown();

															const commandOptionButton = [
																...document.getElementsByClassName('selected-command-option-button')
															]?.at(-1);
															commandOptionButton.scrollIntoView({ block: 'center' });
														}

														if (commandsContainerElement && e.key === 'Tab') {
															e.preventDefault();

															const commandOptionButton = [
																...document.getElementsByClassName('selected-command-option-button')
															]?.at(-1);

															commandOptionButton?.click();
														}

														if (commandsContainerElement && e.key === 'Enter') {
															e.preventDefault();

															const commandOptionButton = [
																...document.getElementsByClassName('selected-command-option-button')
															]?.at(-1);

															if (commandOptionButton) {
																commandOptionButton?.click();
															} else {
																document.getElementById('send-message-button')?.click();
															}
														}
													} else {
														if (
															!$mobile ||
															!(
																'ontouchstart' in window ||
																navigator.maxTouchPoints > 0 ||
																navigator.msMaxTouchPoints > 0
															)
														) {
															if (isComposing) {
																return;
															}

															// Uses keyCode '13' for Enter key for chinese/japanese keyboards.
															//
															// Depending on the user's settings, it will send the message
															// either when Enter is pressed or when Ctrl+Enter is pressed.
															const enterPressed =
																($settings?.ctrlEnterToSend ?? false)
																	? (e.key === 'Enter' || e.keyCode === 13) && isCtrlPressed
																	: (e.key === 'Enter' || e.keyCode === 13) && !e.shiftKey;

															if (enterPressed) {
																e.preventDefault();
																if (prompt !== '' || files.length > 0) {
																	// 检查是否必须上传附件
																	if (requireAttachment && (!files || files.length === 0)) {
																		const attachmentTypeText = attachmentUploadType === 'file' ? '文件' : 
																									attachmentUploadType === 'image' ? '图片' : '附件';
																		toast.error(`此应用必须上传${attachmentTypeText}才能发送消息`);
																		return;
																	}
																	dispatch('submit', prompt);
																}
															}
														}
													}

													if (e.key === 'Escape') {
														console.log('Escape');
														atSelectedModel = undefined;
														selectedToolIds = [];
														webSearchEnabled = false;
														imageGenerationEnabled = false;
													}
												}}
												on:paste={async (e) => {
													e = e.detail.event;
													console.log(e);

													const clipboardData = e.clipboardData || window.clipboardData;

													if (clipboardData && clipboardData.items) {
														for (const item of clipboardData.items) {
															if (item.type.indexOf('image') !== -1) {
																// 检查图片上传限制
																const currentImages = (files ?? []).filter((f) => f?.type === 'image');
																const limit = imageUploadLimit ?? Infinity;
																const remaining = Math.max(0, limit - currentImages.length);

																if (remaining <= 0) {
																	toast.warning('超过图片上传上限');
																	return;
																}

																const blob = item.getAsFile();
																const reader = new FileReader();

																reader.onload = function (e) {
																	files = [
																		...files,
																		{
																			type: 'image',
																			url: `${e.target.result}`
																		}
																	];
																};

																reader.readAsDataURL(blob);
															} else if (item.type === 'text/plain') {
																if ($settings?.largeTextAsFile ?? false) {
																	const text = clipboardData.getData('text/plain');

																	if (text.length > PASTED_TEXT_CHARACTER_LIMIT) {
																		// 检查文件上传限制
																		const currentFiles = (files ?? []).filter((f) => f?.type !== 'image');
																		const currentImages = (files ?? []).filter((f) => f?.type === 'image');
																		const limit = fileUploadLimit ?? Infinity;
																		const remaining = Math.max(0, limit - currentFiles.length - currentImages.length);

																		if (remaining <= 0) {
																			toast.warning('超过文件上传上限');
																			return;
																		}

																		e.preventDefault();
																		const blob = new Blob([text], { type: 'text/plain' });
																		const file = new File([blob], `Pasted_Text_${Date.now()}.txt`, {
																			type: 'text/plain'
																		});

																		await uploadFileHandler(file, true);
																	}
																}
															}
														}
													}
												}}
											/>
										</div>
									{:else}
										<textarea
											id="chat-input"
											dir="auto"
											bind:this={chatInputElement}
											class="scrollbar-hidden bg-transparent dark:text-gray-100 outline-hidden w-full pt-3 px-1 resize-none"
											placeholder={placeholder ? placeholder : $i18n.t('Send a Message')}
											bind:value={prompt}
											on:compositionstart={() => (isComposing = true)}
											on:compositionend={() => (isComposing = false)}
											on:keydown={async (e) => {
												const isCtrlPressed = e.ctrlKey || e.metaKey; // metaKey is for Cmd key on Mac

												const commandsContainerElement =
													document.getElementById('commands-container');

												if (e.key === 'Escape') {
													stopResponse();
												}

												// Command/Ctrl + Shift + Enter to submit a message pair
												if (isCtrlPressed && e.key === 'Enter' && e.shiftKey) {
													e.preventDefault();
													createMessagePair(prompt);
												}

												// Check if Ctrl + R is pressed
												if (prompt === '' && isCtrlPressed && e.key.toLowerCase() === 'r') {
													e.preventDefault();
													console.log('regenerate');

													const regenerateButton = [
														...document.getElementsByClassName('regenerate-response-button')
													]?.at(-1);

													regenerateButton?.click();
												}

												if (prompt === '' && e.key == 'ArrowUp') {
													e.preventDefault();

													const userMessageElement = [
														...document.getElementsByClassName('user-message')
													]?.at(-1);

													const editButton = [
														...document.getElementsByClassName('edit-user-message-button')
													]?.at(-1);

													console.log(userMessageElement);

													userMessageElement.scrollIntoView({ block: 'center' });
													editButton?.click();
												}

												if (commandsContainerElement) {
													if (commandsContainerElement && e.key === 'ArrowUp') {
														e.preventDefault();
														commandsElement.selectUp();

														const commandOptionButton = [
															...document.getElementsByClassName('selected-command-option-button')
														]?.at(-1);
														commandOptionButton.scrollIntoView({ block: 'center' });
													}

													if (commandsContainerElement && e.key === 'ArrowDown') {
														e.preventDefault();
														commandsElement.selectDown();

														const commandOptionButton = [
															...document.getElementsByClassName('selected-command-option-button')
														]?.at(-1);
														commandOptionButton.scrollIntoView({ block: 'center' });
													}

													if (commandsContainerElement && e.key === 'Enter') {
														e.preventDefault();

														const commandOptionButton = [
															...document.getElementsByClassName('selected-command-option-button')
														]?.at(-1);

														if (e.shiftKey) {
															prompt = `${prompt}\n`;
														} else if (commandOptionButton) {
															commandOptionButton?.click();
														} else {
															document.getElementById('send-message-button')?.click();
														}
													}

													if (commandsContainerElement && e.key === 'Tab') {
														e.preventDefault();

														const commandOptionButton = [
															...document.getElementsByClassName('selected-command-option-button')
														]?.at(-1);

														commandOptionButton?.click();
													}
												} else {
													if (
														!$mobile ||
														!(
															'ontouchstart' in window ||
															navigator.maxTouchPoints > 0 ||
															navigator.msMaxTouchPoints > 0
														)
													) {
														if (isComposing) {
															return;
														}

														// Prevent Enter key from creating a new line
														const isCtrlPressed = e.ctrlKey || e.metaKey;
														const enterPressed =
															($settings?.ctrlEnterToSend ?? false)
																? (e.key === 'Enter' || e.keyCode === 13) && isCtrlPressed
																: (e.key === 'Enter' || e.keyCode === 13) && !e.shiftKey;

														console.log('Enter pressed:', enterPressed);

														if (enterPressed) {
															e.preventDefault();
														}

														// Submit the prompt when Enter key is pressed
														if ((prompt !== '' || files.length > 0) && enterPressed) {
															// 检查是否必须上传附件
															if (requireAttachment && (!files || files.length === 0)) {
																const attachmentTypeText = attachmentUploadType === 'file' ? '文件' : 
																							attachmentUploadType === 'image' ? '图片' : '附件';
																toast.error(`此应用必须上传${attachmentTypeText}才能发送消息`);
																return;
															}
															dispatch('submit', prompt);
														}
													}
												}

												if (e.key === 'Tab') {
													const words = extractCurlyBraceWords(prompt);

													if (words.length > 0) {
														const word = words.at(0);
														const fullPrompt = prompt;

														prompt = prompt.substring(0, word?.endIndex + 1);
														await tick();

														e.target.scrollTop = e.target.scrollHeight;
														prompt = fullPrompt;
														await tick();

														e.preventDefault();
														e.target.setSelectionRange(word?.startIndex, word.endIndex + 1);
													}

													e.target.style.height = '';
													e.target.style.height = Math.min(e.target.scrollHeight, 320) + 'px';
												}

												if (e.key === 'Escape') {
													console.log('Escape');
													atSelectedModel = undefined;
													selectedToolIds = [];
													webSearchEnabled = false;
													imageGenerationEnabled = false;
												}
											}}
											rows="1"
											on:input={async (e) => {
												e.target.style.height = '';
												e.target.style.height = Math.min(e.target.scrollHeight, 320) + 'px';
											}}
											on:focus={async (e) => {
												e.target.style.height = '';
												e.target.style.height = Math.min(e.target.scrollHeight, 320) + 'px';
											}}
											on:paste={async (e) => {
												const clipboardData = e.clipboardData || window.clipboardData;

												if (clipboardData && clipboardData.items) {
													for (const item of clipboardData.items) {
														if (item.type.indexOf('image') !== -1) {
															// 检查图片上传限制
															const currentImages = (files ?? []).filter((f) => f?.type === 'image');
															const limit = imageUploadLimit ?? Infinity;
															const remaining = Math.max(0, limit - currentImages.length);

															if (remaining <= 0) {
																toast.warning('超过图片上传上限');
																return;
															}

															const blob = item.getAsFile();
															const reader = new FileReader();

															reader.onload = function (e) {
																files = [
																	...files,
																	{
																		type: 'image',
																		url: `${e.target.result}`
																	}
																];
															};

															reader.readAsDataURL(blob);
														} else if (item.type === 'text/plain') {
															if ($settings?.largeTextAsFile ?? false) {
																const text = clipboardData.getData('text/plain');

																if (text.length > PASTED_TEXT_CHARACTER_LIMIT) {
																	// 检查文件上传限制
																	const currentFiles = (files ?? []).filter((f) => f?.type !== 'image');
																	const currentImages = (files ?? []).filter((f) => f?.type === 'image');
																	const limit = fileUploadLimit ?? Infinity;
																	const remaining = Math.max(0, limit - currentFiles.length - currentImages.length);

																	if (remaining <= 0) {
																		toast.warning('超过文件上传上限');
																		return;
																	}

																	e.preventDefault();
																	const blob = new Blob([text], { type: 'text/plain' });
																	const file = new File([blob], `Pasted_Text_${Date.now()}.txt`, {
																		type: 'text/plain'
																	});

																	await uploadFileHandler(file, true);
																}
															}
														}
													}
												}
											}}
										/>
									{/if}
								</div>
								{/if}

								<div class=" flex justify-between mt-1 mb-2.5 mx-0.5 max-w-full" dir="ltr">
									<div class="ml-1 self-end flex items-start flex-1 max-w-[80%] gap-0.5">
										{#if showFileUploadButton || showImageUploadButton}
											<InputMenu
												bind:selectedToolIds
												{screenCaptureHandler}
												{inputFilesHandler}
												{showImageUploadButton}
												{showFileUploadButton}
												{fileUploadLimit}
												{imageUploadLimit}
												{files}
												uploadFilesHandler={() => {
													filesInputElement.click();
												}}
												uploadGoogleDriveHandler={async () => {
													try {
														const fileData = await createPicker();
														if (fileData) {
															const file = new File([fileData.blob], fileData.name, {
																type: fileData.blob.type
															});
															await uploadFileHandler(file);
														} else {
															console.log('No file was selected from Google Drive');
														}
													} catch (error) {
														console.error('Google Drive Error:', error);
														toast.error(
															$i18n.t('Error accessing Google Drive: {{error}}', {
																error: error.message
															})
														);
													}
												}}
												uploadOneDriveHandler={async () => {
													try {
														const fileData = await pickAndDownloadFile();
														if (fileData) {
															const file = new File([fileData.blob], fileData.name, {
																type: fileData.blob.type || 'application/octet-stream'
															});
															await uploadFileHandler(file);
														} else {
															console.log('No file was selected from OneDrive');
														}
													} catch (error) {
														console.error('OneDrive Error:', error);
													}
												}}
												onClose={async () => {
													await tick();

													const chatInput = document.getElementById('chat-input');
													chatInput?.focus();
												}}
											>
												<button
													class="bg-transparent hover:bg-gray-100 text-gray-800 dark:text-white dark:hover:bg-gray-800 transition rounded-full p-1.5 outline-hidden focus:outline-hidden"
													type="button"
													aria-label="More"
												>
													<svg
														xmlns="http://www.w3.org/2000/svg"
														viewBox="0 0 20 20"
														fill="currentColor"
														class="size-5"
													>
														<path
															d="M10.75 4.75a.75.75 0 0 0-1.5 0v4.5h-4.5a.75.75 0 0 0 0 1.5h4.5v4.5a.75.75 0 0 0 1.5 0v-4.5h4.5a.75.75 0 0 0 0-1.5h-4.5v-4.5Z"
														/>
													</svg>
												</button>
											</InputMenu>
										{/if}

										<div class="flex gap-1 items-center overflow-x-auto scrollbar-none flex-1">
											{#if toolServers.length + selectedToolIds.length > 0}
												<Tooltip
													content={$i18n.t('{{COUNT}} Available Tools', {
														COUNT: toolServers.length + selectedToolIds.length
													})}
												>
													<button
														class="translate-y-[0.5px] flex gap-1 items-center text-gray-600 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200 rounded-lg p-1 self-center transition"
														aria-label="Available Tools"
														type="button"
														on:click={() => {
															showTools = !showTools;
														}}
													>
														<Wrench className="size-4" strokeWidth="1.75" />

														<span class="text-sm font-medium text-gray-600 dark:text-gray-300">
															{toolServers.length + selectedToolIds.length}
														</span>
													</button>
												</Tooltip>
											{/if}

											{#if $_user}
												{#if $config?.features?.enable_web_search && ($_user.role === 'admin' || $_user?.permissions?.features?.web_search) && showWebSearchButton}
													<Tooltip
														content={$i18n.t('Search the internet')}
														placement="top"
													>
														<button
															on:click|preventDefault={() => {
																webSearchEnabled = !webSearchEnabled;
															}}
															type="button"
															class="px-1.5 @xl:px-2.5 py-1.5 flex gap-1.5 items-center text-sm rounded-full font-medium transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden border {webSearchEnabled ||
															($settings?.webSearch ?? false) === 'always'
																? 'bg-primary-100 dark:bg-primary-500/20 border-primary-400/20 text-primary-500 dark:text-primary-400'
																: 'bg-transparent border-transparent text-gray-600 dark:text-gray-300 border-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'} {isRagFlowModel
																? 'opacity-50 cursor-not-allowed'
																: ''}"
														>
															<GlobeAlt className="size-5" strokeWidth="1.75" />
															<span
																class="hidden @xl:block whitespace-nowrap overflow-hidden text-ellipsis translate-y-[0.5px]"
																>搜索</span
															>
														</button>
													</Tooltip>
												{/if}

												<!-- 知识库选择器 - 只在选择 rag_flow_webapi_pipeline_cs 模型时显示 -->
												{#if showKnowledgeBaseButton || showKbWebSearchButton || showEnhancedSearchButton || showDeepResearchButton}
													<KnowledgeBaseSelector
														selectedModelId={selectedModelIds[0]}
														assistantId={$_user.assistant_id}
														{showKnowledgeBaseButton}
														{showKbWebSearchButton}
														{showEnhancedSearchButton}
														{showDeepResearchButton}
														on:kbIdsChange={(e) => {
															kb_ids = e.detail.kb_ids;
															console.log('kb_ids updated:', kb_ids);
														}}
													/>
												{/if}

												{#if $config?.features?.enable_image_generation && ($_user.role === 'admin' || $_user?.permissions?.features?.image_generation)}
													<Tooltip content={$i18n.t('Generate an image')} placement="top">
														<button
															on:click|preventDefault={() =>
																(imageGenerationEnabled = !imageGenerationEnabled)}
															type="button"
															class="px-1.5 @xl:px-2.5 py-1.5 flex gap-1.5 items-center text-sm rounded-full font-medium transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden border {imageGenerationEnabled
																? 'bg-gray-50 dark:bg-gray-400/10 border-gray-100 dark:border-gray-700 text-gray-600 dark:text-gray-400'
																: 'bg-transparent border-transparent text-gray-600 dark:text-gray-300  hover:bg-gray-100 dark:hover:bg-gray-800 '}"
														>
															<Photo className="size-5" strokeWidth="1.75" />
															<span
																class="hidden @xl:block whitespace-nowrap overflow-hidden text-ellipsis translate-y-[0.5px]"
																>{$i18n.t('Image')}</span
															>
														</button>
													</Tooltip>
												{/if}

												{#if $config?.features?.enable_code_interpreter && ($_user.role === 'admin' || $_user?.permissions?.features?.code_interpreter)}
													<Tooltip content={$i18n.t('Execute code for analysis')} placement="top">
														<button
															on:click|preventDefault={() =>
																(codeInterpreterEnabled = !codeInterpreterEnabled)}
															type="button"
															class="px-1.5 @xl:px-2.5 py-1.5 flex gap-1.5 items-center text-sm rounded-full font-medium transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden border {codeInterpreterEnabled
																? 'bg-gray-50 dark:bg-gray-400/10 border-gray-100  dark:border-gray-700 text-gray-600 dark:text-gray-400  '
																: 'bg-transparent border-transparent text-gray-600 dark:text-gray-300  hover:bg-gray-100 dark:hover:bg-gray-800 '}"
														>
															<CommandLine className="size-5" strokeWidth="1.75" />
															<span
																class="hidden @xl:block whitespace-nowrap overflow-hidden text-ellipsis translate-y-[0.5px]"
																>{$i18n.t('Code Interpreter')}</span
															>
														</button>
													</Tooltip>
												{/if}
											{/if}
										</div>
									</div>

									<div class="self-end flex space-x-1 mr-1 shrink-0">
										{#if $showPressToTalk}
											<!-- 按住说话模式：显示键盘输入按钮 -->
											<Tooltip content="键盘输入">
												<button
													id="keyboard-input-button"
													class=" text-gray-600 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200 transition rounded-full p-1.5 mr-0.5 self-center"
													type="button"
													on:click={() => {
														$showPressToTalk = false;
														recording = false;
														prompt = promptText;
														promptText = '';
													}}
													aria-label="Keyboard Input"
												>
													<svg
														xmlns="http://www.w3.org/2000/svg"
														fill="none"
														viewBox="0 0 24 24"
														stroke-width="1.5"
														stroke="currentColor"
														class="w-5 h-5"
													>
														<path stroke-linecap="round" stroke-linejoin="round" d="M3 8.25V17c0 .966.784 1.75 1.75 1.75h14.5A1.75 1.75 0 0021 17V8.25M3 8.25V6.75A1.75 1.75 0 014.75 5h14.5c.966 0 1.75.784 1.75 1.75V8.25M3 8.25h18M7.5 10.5v1M12 10.5v1M16.5 10.5v1M7.5 14.5v1M12 14.5v1M16.5 14.5v1" />
													</svg>
												</button>
											</Tooltip>
										{:else if !history?.currentId || history.messages[history.currentId]?.done == true}
											<Tooltip content={$i18n.t('Record voice')}>
												<button
													id="voice-input-button"
													class=" text-gray-600 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200 transition rounded-full p-1.5 mr-0.5 self-center"
													type="button"
													on:click={async () => {
														try {
															let stream = await navigator.mediaDevices
																.getUserMedia({ audio: true })
																.catch(function (err) {
																	toast.error(
																		$i18n.t(
																			`Permission denied when accessing microphone: {{error}}`,
																			{
																				error: err
																			}
																		)
																	);
																	return null;
																});

															if (stream) {
																if($mobile) {
																	$showPressToTalk = true;
																}
																recording = true;
																const tracks = stream.getTracks();
																tracks.forEach((track) => track.stop());
																promptText = prompt;
																prompt = '';
															}
															stream = null;
														} catch {
															toast.error($i18n.t('Permission denied when accessing microphone'));
														}
													}}
													aria-label="Voice Input"
												>
													<svg
														xmlns="http://www.w3.org/2000/svg"
														viewBox="0 0 20 20"
														fill="currentColor"
														class="w-5 h-5 translate-y-[0.5px]"
													>
														<path d="M7 4a3 3 0 016 0v6a3 3 0 11-6 0V4z" />
														<path
															d="M5.5 9.643a.75.75 0 00-1.5 0V10c0 3.06 2.29 5.585 5.25 5.954V17.5h-1.5a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-1.5v-1.546A6.001 6.001 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-9 0v-.357z"
														/>
													</svg>
												</button>
											</Tooltip>
										{/if}

										{#if !history.currentId || history.messages[history.currentId]?.done == true}
											{#if prompt === '' && files.length === 0}
												<div class=" flex items-center">
													<!-- 移除通话按钮，因为在没有输入时也不需要显示通话按钮 -->
													<!--
													<Tooltip content={$i18n.t('Call')}>
														<button
															class=" {webSearchEnabled ||
															($settings?.webSearch ?? false) === 'always'
																? 'bg-blue-500 text-white hover:bg-blue-400 '
																: 'bg-black text-white hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100'} transition rounded-full p-1.5 self-center"
															type="button"
															on:click={async () => {
																if (selectedModels.length > 1) {
																	toast.error($i18n.t('Select only one model to call'));

																	return;
																}

																if ($config.audio.stt.engine === 'web') {
																	toast.error(
																		$i18n.t(
																			'Call feature is not supported when using Web STT engine'
																		)
																	);

																	return;
																}
																// check if user has access to getUserMedia
																try {
																	let stream = await navigator.mediaDevices.getUserMedia({
																		audio: true
																	});
																	// If the user grants the permission, proceed to show the call overlay

																	if (stream) {
																		const tracks = stream.getTracks();
																		tracks.forEach((track) => track.stop());
																	}

																	stream = null;

																	if ($settings.audio?.tts?.engine === 'browser-kokoro') {
																		// If the user has not initialized the TTS worker, initialize it
																		if (!$TTSWorker) {
																			await TTSWorker.set(
																				new KokoroWorker({
																					dtype: $settings.audio?.tts?.engineConfig?.dtype ?? 'fp32'
																				})
																			);

																			await $TTSWorker.init();
																		}
																	}

																	showCallOverlay.set(true);
																	showControls.set(true);
																} catch (err) {
																	// If the user denies the permission or an error occurs, show an error message
																	toast.error(
																		$i18n.t('Permission denied when accessing media devices')
																	);
																}
															}}
															aria-label="Call"
														>
															<Headphone className="size-5" />
														</button>
													</Tooltip>
													-->
													<!-- 在没有输入时也显示发送按钮，只是禁用状态 -->
													<Tooltip content={$i18n.t('Send message')}>
														<button
															id="send-message-button"
															class="{$showPressToTalk ? 'hidden' : 'text-white bg-gray-200 dark:text-gray-900 dark:bg-gray-700 disabled transition rounded-full p-1.5 self-center'}"
															type="submit"
															disabled={true}
														>
															<svg
																xmlns="http://www.w3.org/2000/svg"
																viewBox="0 0 16 16"
																fill="currentColor"
																class="size-5"
															>
																<path
																	fill-rule="evenodd"
																	d="M8 14a.75.75 0 0 1-.75-.75V4.56L4.03 7.78a.75.75 0 0 1-1.06-1.06l4.5-4.5a.75.75 0 0 1 1.06 0l4.5 4.5a.75.75 0 0 1-1.06 1.06L8.75 4.56v8.69A.75.75 0 0 1 8 14Z"
																	clip-rule="evenodd"
																/>
															</svg>
														</button>
													</Tooltip>
												</div>
											{:else}
												<div class=" flex items-center">
													<Tooltip content={$i18n.t('Send message')}>
														<button
															id="send-message-button"
															class="{$showPressToTalk ? 'hidden' : !(prompt === '' && files.length === 0)
																? webSearchEnabled || ($settings?.webSearch ?? false) === 'always'
																	? 'bg-primary-500 text-white hover:bg-primary-400 '
																	: 'bg-black text-white hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100 '
																: 'text-white bg-gray-200 dark:text-gray-900 dark:bg-gray-700 disabled'} transition rounded-full p-1.5 self-center"
															type="submit"
															disabled={prompt === '' && files.length === 0}
														>
															<svg
																xmlns="http://www.w3.org/2000/svg"
																viewBox="0 0 16 16"
																fill="currentColor"
																class="size-5"
															>
																<path
																	fill-rule="evenodd"
																	d="M8 14a.75.75 0 0 1-.75-.75V4.56L4.03 7.78a.75.75 0 0 1-1.06-1.06l4.5-4.5a.75.75 0 0 1 1.06 0l4.5 4.5a.75.75 0 0 1-1.06 1.06L8.75 4.56v8.69A.75.75 0 0 1 8 14Z"
																	clip-rule="evenodd"
																/>
															</svg>
														</button>
													</Tooltip>
												</div>
											{/if}
										{:else}
											<div class=" flex items-center">
												<Tooltip content={$i18n.t('Stop')}>
													<button
														class="bg-white hover:bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-white dark:hover:bg-gray-800 transition rounded-full p-1.5"
														on:click={() => {
															stopResponse();
														}}
													>
														<svg
															xmlns="http://www.w3.org/2000/svg"
															viewBox="0 0 24 24"
															fill="currentColor"
															class="size-5"
														>
															<path
																fill-rule="evenodd"
																d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm6-2.438c0-.724.588-1.312 1.313-1.312h4.874c.725 0 1.313.588 1.313 1.313v4.874c0 .725-.588 1.313-1.313 1.313H9.564a1.312 1.312 0 01-1.313-1.313V9.564z"
																clip-rule="evenodd"
															/>
														</svg>
													</button>
												</Tooltip>
											</div>
										{/if}
									</div>
								</div>
							</div>
						</form>
				</div>
			</div>
		</div>
	</div>
{/if}
