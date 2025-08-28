<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { createEventDispatcher } from 'svelte';
	import { parseChangelog, type ChangelogVersion } from '$lib/utils';
	import { marked } from 'marked';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	// 当前版本号
	let version = "";
	
	// 更新日志相关状态
	let changelogVersions: ChangelogVersion[] = [];
	let selectedVersion: string = '';
	let selectedVersionData: ChangelogVersion | null = null;
	let changelogLoading = false;

	// 加载更新日志
	const loadChangelog = async () => {
		changelogLoading = true;
		try {
			const response = await fetch('/XIAOZHI_CHANGELOG.md');
			if (response.ok) {
				const content = await response.text();
				changelogVersions = parseChangelog(content);
				if (changelogVersions.length > 0) {
					selectedVersion = changelogVersions[0].version;
					selectedVersionData = changelogVersions[0];
					version = changelogVersions[0].version;
				}
			}
		} catch (error) {
			console.error('Failed to load changelog:', error);
		} finally {
			changelogLoading = false;
		}
	};

	// 处理版本选择
	const onVersionSelect = (event: Event) => {
		const target = event.target as HTMLSelectElement;
		selectedVersion = target.value;
		selectedVersionData = changelogVersions.find(v => v.version === selectedVersion) || null;
	};

	onMount(loadChangelog);
</script>

<div class="flex flex-col h-full justify-between space-y-3 text-sm">
	<div class="space-y-3 overflow-y-scroll max-h-[28rem] lg:max-h-full">
		<div>
			<div class="mb-1.5 text-sm font-medium">{$i18n.t('Version')}</div>
			<div class="py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
				<div class="flex items-center">
					<span class="text-base font-medium">当前版本: v{version}</span>
				</div>
			</div>
		</div>

		<!-- 更新日志部分 -->
		<div>
			<!-- 标题和版本选择器在同一行 -->
			<div class="flex items-center justify-between mb-1.5">
				<div class="text-sm font-medium">更新日志</div>
				{#if changelogVersions.length > 0}
					<select 
						bind:value={selectedVersion}
						on:change={onVersionSelect}
						class="w-15 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-xs"
					>
						{#each changelogVersions as versionItem}
							<option value={versionItem.version}>
								v{versionItem.version}
							</option>
						{/each}
					</select>
				{/if}
			</div>

			{#if changelogLoading}
				<div class="py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
					<span class="text-sm text-gray-600 dark:text-gray-400">加载中...</span>
				</div>
			{:else if changelogVersions.length > 0}
				<!-- 选中版本的更新信息 -->
				{#if selectedVersionData}
					<div class="max-h-[21rem] overflow-y-auto py-3 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
						<div class="mb-2">
							<span class="text-sm font-medium text-gray-900 dark:text-gray-100">
								v{selectedVersionData.version}
							</span>
							<span class="text-xs text-gray-500 dark:text-gray-400 ml-2">
								{selectedVersionData.date}
							</span>
						</div>
						<div class="prose prose-sm dark:prose-invert max-w-none text-gray-700 dark:text-gray-300">
							{@html marked(selectedVersionData.content)}
						</div>
					</div>
				{/if}
			{:else}
				<div class="py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
					<span class="text-sm text-gray-600 dark:text-gray-400">未找到更新日志</span>
				</div>
			{/if}
		</div>
	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
			on:click={() => {
				dispatch('save');
			}}
		>
			{$i18n.t('Close')}
		</button>
	</div>
</div> 