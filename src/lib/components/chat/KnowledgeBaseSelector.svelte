<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { DropdownMenu } from 'bits-ui';
	import { flyAndScale } from '$lib/utils/transitions';
	import { getAssistantInfo, updateAssistantKnowledgeBases, updateAssistantTavily } from '$lib/apis/ragflow';
	import type { AssistantInfo } from '$lib/apis/ragflow';
	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import GlobeAlt from '../icons/GlobeAlt.svelte';
	export let selectedModelId: string = '';
	export let assistantId: string = '';

	let assistantInfo: AssistantInfo | null = null;
	let loading = false;
	let showKnowledgeBasePanel = false;
	let showTavilyPanel = false;
	let selectedKbIds: string[] = [];
	let tavilyApiKey = '';
	let tavilyEnabled = false;

	// 只在选择rag_flow_webapi_pipeline_cs模型时显示
	$: shouldShow = selectedModelId === 'rag_flow_webapi_pipeline_cs';

	// 监听模型变化，加载assistant信息
	$: if (shouldShow) {
		loadAssistantInfo();
	}

	async function loadAssistantInfo() {
		console.log('loadAssistantInfo', assistantId, localStorage.token);
		if (!assistantId || !localStorage.token) return;

		loading = true;
		try {
			assistantInfo = await getAssistantInfo(localStorage.token, assistantId);
			selectedKbIds = [...assistantInfo.kb_ids];
			tavilyApiKey = assistantInfo.tavily_api_key || '';
			tavilyEnabled = assistantInfo.tavily_enabled;
		} catch (error) {
			console.error('Failed to load assistant info:', error);
			toast.error('Failed to load assistant configuration');
		} finally {
			loading = false;
		}
	}

	function toggleTavilyPanel() {
		showTavilyPanel = !showTavilyPanel;
		if (showTavilyPanel) {
			showKnowledgeBasePanel = false;
		}
	}

	async function toggleKnowledgeBase(kbId: string) {
		const isCurrentlySelected = selectedKbIds.includes(kbId);
		let newKbIds: string[];

		if (isCurrentlySelected) {
			newKbIds = selectedKbIds.filter(id => id !== kbId);
		} else {
			newKbIds = [...selectedKbIds, kbId];
		}

		// 乐观更新
		const previousKbIds = [...selectedKbIds];
		selectedKbIds = newKbIds;

		try {
			await updateAssistantKnowledgeBases(localStorage.token, {
				assistant_id: assistantId,
				kb_ids: newKbIds
			});
			toast.success('Knowledge base configuration updated');
		} catch (error) {
			// 回滚更改
			selectedKbIds = previousKbIds;
			console.error('Failed to update knowledge bases:', error);
			toast.error('Failed to update knowledge base configuration');
		}
	}

	async function toggleTavily() {
		const newTavilyEnabled = !tavilyEnabled;
		
		// 乐观更新
		const previousTavilyEnabled = tavilyEnabled;
		tavilyEnabled = newTavilyEnabled;

		try {
			await updateAssistantTavily(localStorage.token, {
				assistant_id: assistantId,
				tavily_enabled: newTavilyEnabled
			});
			toast.success(`Web search ${newTavilyEnabled ? 'enabled' : 'disabled'}`);
		} catch (error) {
			// 回滚更改
			tavilyEnabled = previousTavilyEnabled;
			console.error('Failed to update tavily config:', error);
			toast.error('Failed to update web search configuration');
		}
	}

	function closeAllPanels() {
		showKnowledgeBasePanel = false;
		showTavilyPanel = false;
	}
</script>

<!-- 只在rag_flow_webapi_pipeline_cs模型时显示 -->
{#if shouldShow}
	<div class="ragflow-container inline-flex items-center gap-1">
		<!-- 联网搜索按钮 - 参考Web Search样式 -->
		<button
			on:click={toggleTavily}
			type="button"
			class="px-1.5 @xl:px-2.5 py-1.5 flex gap-1.5 items-center text-sm rounded-full font-medium transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden border {tavilyEnabled
				? 'bg-primary-100 dark:bg-primary-500/20 border-primary-400/20 text-primary-500 dark:text-primary-400'
				: 'bg-transparent border-transparent text-gray-600 dark:text-gray-300 border-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'}"
			disabled={loading || !assistantInfo}
		>
			<GlobeAlt className="size-5" strokeWidth="1.75" />
			<span class="hidden @xl:block whitespace-nowrap overflow-hidden text-ellipsis translate-y-[0.5px]">联网搜索</span>
		</button>

		<!-- 知识库选择按钮 - 使用Dropdown组件，参考InputMenu样式 -->
		<Dropdown
			bind:show={showKnowledgeBasePanel}
			on:change={(e) => {
				if (e.detail === false) {
					showKnowledgeBasePanel = false;
				}
			}}
		>
			<button
				type="button"
				class="px-1.5 @xl:px-2.5 py-1.5 flex gap-1.5 items-center text-sm rounded-full font-medium transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden border {selectedKbIds.length > 0 || showKnowledgeBasePanel
					? 'bg-primary-100 dark:bg-primary-500/20 border-primary-400/20 text-primary-500 dark:text-primary-400'
					: 'bg-transparent border-transparent text-gray-600 dark:text-gray-300 border-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'}"
				disabled={loading || !assistantInfo}
			>
				<svg class="size-5" stroke-width="1.75" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" 
						d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012 2v2M7 7h10" />
				</svg>
				<span class="hidden @xl:block whitespace-nowrap overflow-hidden text-ellipsis translate-y-[0.5px]">知识库选择</span>
				{#if assistantInfo && assistantInfo.knowledge_bases.length > 0}
					<span class="ml-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-1.5 py-0.5 rounded-full text-xs font-medium">
						{selectedKbIds.length}/{assistantInfo.knowledge_bases.length}
					</span>
				{/if}
			</button>

			<div slot="content">
				<DropdownMenu.Content
					class="w-full max-w-[200px] rounded-xl px-1 py-1 border border-gray-300/30 dark:border-gray-700/50 z-50 bg-white dark:bg-gray-850 dark:text-white shadow-sm"
					sideOffset={10}
					alignOffset={-8}
					side="top"
					align="start"
					transition={flyAndScale}
				>
					{#if assistantInfo && assistantInfo.knowledge_bases.length === 0}
						<div class="px-3 py-2 text-center">
							<p class="text-gray-500 dark:text-gray-400 text-sm">暂无可用知识库</p>
						</div>
					{:else if assistantInfo}
						<div class="max-h-28 overflow-y-auto scrollbar-hidden">
							{#each assistantInfo.knowledge_bases as kb}
								<button
									class="flex w-full justify-between gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800"
									on:click={() => toggleKnowledgeBase(kb.kb_id)}
								>
									<div class="flex-1 truncate">
										<div class="flex flex-1 gap-2 items-center">
											<div class="shrink-0">
												<svg class="w-4 h-4" stroke-width="1.75" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" 
														d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012 2v2M7 7h10" />
												</svg>
											</div>
											<div class="truncate" title={kb.kb_name}>{kb.kb_name}</div>
										</div>
									</div>

									<div class="shrink-0">
										<div class="w-10 h-5 bg-gray-200 dark:bg-gray-600 rounded-full relative transition-colors duration-200 {selectedKbIds.includes(kb.kb_id) ? 'bg-primary-500 dark:bg-primary-500' : ''}">
											<div class="w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform duration-200 {selectedKbIds.includes(kb.kb_id) ? 'translate-x-5' : 'translate-x-0.5'}"></div>
										</div>
									</div>
								</button>
							{/each}
						</div>
					{/if}
				</DropdownMenu.Content>
			</div>
		</Dropdown>

		<!-- Loading图标 - 与其他按钮在同一水平线 -->
		{#if loading}
			<div class="loading-container">
				<svg class="size-4 animate-spin text-gray-600 dark:text-gray-300" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
				</svg>
			</div>
		{/if}
	</div>
{/if}

<style>
	.ragflow-container {
		position: relative;
	}

	.loading-container {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 4px;
	}
</style>