<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	export let outlineData: any = null;
	export let editable = true;

	const dispatch = createEventDispatcher();

	interface OutlineItem {
		id: string;
		text: string;
		level: number; // 1, 2, 3
		parent?: string;
		children?: string[];
	}

	let items: OutlineItem[] = [];
	let focusedItemId: string | null = null;

	// 将JSON数据转换为平铺的items数组
	function parseOutlineData(data: any) {
		if (!data || !data.outline) return;

		const newItems: OutlineItem[] = [];
		let idCounter = 0;

		data.outline.forEach((section: any) => {
			// 一级标题
			const sectionId = `item-${idCounter++}`;
			newItems.push({
				id: sectionId,
				text: section.title,
				level: 1
			});

			if (section.subsections) {
				section.subsections.forEach((subsection: any) => {
					// 二级标题
					const subsectionId = `item-${idCounter++}`;
					newItems.push({
						id: subsectionId,
						text: subsection.title,
						level: 2
					});

					if (subsection.subpoints) {
						subsection.subpoints.forEach((subpoint: string) => {
							// 三级标题
							const subpointId = `item-${idCounter++}`;
							newItems.push({
								id: subpointId,
								text: subpoint,
								level: 3
							});
						});
					}
				});
			}
		});

		items = newItems;
	}

	// 处理键盘事件
	function handleKeyDown(event: KeyboardEvent, itemId: string) {
		const itemIndex = items.findIndex(item => item.id === itemId);
		if (itemIndex === -1) return;

		switch (event.key) {
			case 'Tab':
				event.preventDefault();
				if (event.shiftKey) {
					// Shift + Tab: 升级
					upgradeItem(itemIndex);
				} else {
					// Tab: 降级
					downgradeItem(itemIndex);
				}
				break;
			case 'Enter':
				event.preventDefault();
				addNewItem(itemIndex);
				break;
			case 'Backspace':
				if (items[itemIndex].text.trim() === '') {
					event.preventDefault();
					deleteItem(itemIndex);
				}
				break;
		}
	}

	// 降级（增加缩进级别）
	function downgradeItem(index: number) {
		if (index === 0) return; // 第一项不能降级
		
		const item = items[index];
		if (item.level >= 3) return; // 最多三级
		
		items[index] = { ...item, level: item.level + 1 };
		dispatch('change', items);
	}

	// 升级（减少缩进级别）
	function upgradeItem(index: number) {
		if (index === 0) return; // 第一项不能升级
		
		const item = items[index];
		if (item.level <= 1) return; // 最少一级
		
		items[index] = { ...item, level: item.level - 1 };
		dispatch('change', items);
	}

	// 添加新项目
	function addNewItem(index: number) {
		const currentItem = items[index];
		const newId = `item-${Date.now()}`;
		const newItem: OutlineItem = {
			id: newId,
			text: '',
			level: currentItem.level
		};

		items.splice(index + 1, 0, newItem);
		items = [...items];
		
		// 聚焦到新项目
		setTimeout(() => {
			const newElement = document.getElementById(newId);
			if (newElement) {
				newElement.focus();
			}
		}, 0);

		dispatch('change', items);
	}

	// 删除项目
	function deleteItem(index: number) {
        if (index == 0) {
            toast.error('不能删除第一项!');
            return;
        }

		// if (items.length <= 1) return; // 至少保留一项
		
		const preIndex = index > 0 ? index - 1 : index;
		items.splice(index, 1);
		items = [...items];
		
		// 聚焦到前一个项目
		if (items.length > 0) {
			setTimeout(() => {
				const preElement = document.getElementById(items[preIndex].id);
				if (preElement) {
					preElement.focus();
				}
			}, 0);
		}
		
		dispatch('change', items);
	}

	// 更新项目文本
	function updateItemText(itemId: string, text: string) {
		const itemIndex = items.findIndex(item => item.id === itemId);
		if (itemIndex !== -1) {
			items[itemIndex] = { ...items[itemIndex], text };
			dispatch('change', items);
		}
	}

	// 获取级别对应的样式类
	function getLevelClass(level: number) {
		switch (level) {
			case 1: return 'text-lg font-bold text-gray-800 dark:text-gray-200 ml-0';
			case 2: return 'text-md font-semibold text-gray-700 dark:text-gray-300 ml-4';
			case 3: return 'text-sm text-gray-600 dark:text-gray-400 ml-8';
			default: return 'text-sm text-gray-600 dark:text-gray-400 ml-0';
		}
	}

	// 获取级别对应的前缀符号
	function getLevelPrefix(level: number, index: number) {
		// 计算分层编号
		const sectionNumbers = getSectionNumbers();
		const currentNumbers = sectionNumbers[index];
		
		if (!currentNumbers) return '';
		
		switch (level) {
			case 1: return `${currentNumbers[0]}. `;
			case 2: return `${currentNumbers[0]}.${currentNumbers[1]} `;
			case 3: return `${currentNumbers[0]}.${currentNumbers[1]}.${currentNumbers[2]} `;
			default: return '• ';
		}
	}

	// 计算所有项目的分层编号
	function getSectionNumbers() {
		const sectionNumbers: number[][] = [];
		let level1Count = 0;
		let level2Count = 0;
		let level3Count = 0;

		items.forEach((item, index) => {
			switch (item.level) {
				case 1:
					level1Count++;
					level2Count = 0;
					level3Count = 0;
					sectionNumbers[index] = [level1Count];
					break;
				case 2:
					level2Count++;
					level3Count = 0;
					sectionNumbers[index] = [level1Count, level2Count];
					break;
				case 3:
					level3Count++;
					sectionNumbers[index] = [level1Count, level2Count, level3Count];
					break;
				default:
					sectionNumbers[index] = [];
			}
		});

		return sectionNumbers;
	}

	// 导出大纲数据
	function exportOutline() {
		return items;
	}

	// 初始化
	onMount(() => {
		if (outlineData) {
			parseOutlineData(outlineData);
		}
	});

	// 监听外部数据变化
	$: if (outlineData) {
		parseOutlineData(outlineData);
	}
</script>

<div class="outline-editor w-full max-w-full p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
	{#if outlineData?.topic}
		<h2 class="text-xl font-bold mb-4 text-gray-800 dark:text-gray-200">
			{outlineData.topic}
		</h2>
	{/if}

	<div class="outline-items space-y-2">
		{#each items as item, index (item.id)}
			<div class="outline-item flex items-start group">
				<span class="prefix text-gray-500 dark:text-gray-400 select-none mr-2 {getLevelClass(item.level)}">
					{getLevelPrefix(item.level, index)}
				</span>
				<div class="flex-1">
					{#if editable}
						<input
							id={item.id}
							type="text"
							class="w-1/3 bg-transparent border-none outline-none resize-none {getLevelClass(item.level)} focus:bg-gray-50 dark:focus:bg-gray-700 px-2 py-1 rounded"
							bind:value={item.text}
							on:input={(e) => updateItemText(item.id, e.target.value)}
							on:keydown={(e) => handleKeyDown(e, item.id)}
							on:focus={() => focusedItemId = item.id}
							on:blur={() => focusedItemId = null}
							placeholder={item.level === 1 ? '一级标题' : item.level === 2 ? '二级标题' : '三级内容'}
						/>
					{:else}
						<div class="{getLevelClass(item.level)} py-1">
							{item.text}
						</div>
					{/if}
				</div>
			</div>
		{/each}
	</div>

	{#if editable}
		<div class="mt-4 text-xs text-gray-500 dark:text-gray-400 space-y-1">
			<div>• <kbd class="bg-gray-100 dark:bg-gray-700 px-1 rounded">Enter</kbd> 新增一行</div>
			<div>• <kbd class="bg-gray-100 dark:bg-gray-700 px-1 rounded">Tab</kbd> 降级</div>
			<div>• <kbd class="bg-gray-100 dark:bg-gray-700 px-1 rounded"> Shift+Tab</kbd> 升级</div>
			<div>• <kbd class="bg-gray-100 dark:bg-gray-700 px-1 rounded">Backspace</kbd> 删除空行</div>
		</div>
	{/if}
</div>

<style>
	.outline-editor {
		font-family: system-ui, -apple-system, sans-serif;
	}
	
	.outline-item:hover {
		background-color: rgba(0, 0, 0, 0.02);
	}
	
	.dark .outline-item:hover {
		background-color: rgba(255, 255, 255, 0.02);
	}
	
	input:focus {
		box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
	}
	
	kbd {
		font-size: 0.75rem;
		padding: 0.125rem 0.25rem;
		border-radius: 0.25rem;
		border: 1px solid #d1d5db;
	}
	
	.dark kbd {
		border-color: #4b5563;
	}
</style> 