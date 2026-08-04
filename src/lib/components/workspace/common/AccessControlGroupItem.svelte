<script lang="ts">
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	import UserCircleSolid from '$lib/components/icons/UserCircleSolid.svelte';
	import ChevronRight from '$lib/components/icons/ChevronRight.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import Checkbox from '$lib/components/common/Checkbox.svelte';
	import Self from './AccessControlGroupItem.svelte';

	export let group: any;
	// 全部权限组列表，用于沿 parent_id 链判断祖先关系
	export let groups: any[] = [];
	// parent_id -> 直属子组列表，用于渲染完整层级树
	export let childrenMap: Record<string, any[]> = {};
	export let accessControl: any = {};
	export let accessRoles: string[] = ['read'];
	export let expandedSet: string[] = [];
	// 已授权组 id 闭包（显式授权组 + 随父组一并授权的子孙组）
	export let selectedClosure: string[] = [];
	export let toggleExpand: Function = () => {};
	export let toggleGroup: Function = () => {};
	export let onToggleWrite: Function = () => {};
	export let level = 0;

	// 完整树：展示全部直属子组（不再按已选闭包过滤）
	$: children = childrenMap[group?.id] ?? [];
	$: hasChildren = children.length > 0;
	$: expanded = expandedSet.includes(group?.id);

	// 某组是否为某组（含其子孙）的后代
	const isDescendantOf = (id: string, ancestorId: string): boolean => {
		let currentId = id;
		while (currentId) {
			if (currentId === ancestorId) return true;
			currentId = groups.find((g) => g.id === currentId)?.parent_id ?? '';
		}
		return false;
	};

	// 该组是否被显式授权（读权限）
	$: explicitlySelected = accessControl?.read?.group_ids?.includes(group?.id) ?? false;

	// 该组是否有后代被授权（用于半选状态）
	$: hasSelectedDescendant = selectedClosure.some((id) => isDescendantOf(id, group?.id));

	// 复选框状态：checked / unchecked / indeterminate
	$: state = explicitlySelected ? 'checked' : hasSelectedDescendant ? 'indeterminate' : 'unchecked';

	// 该组是否被授权（自身选中或随父组继承）
	$: granted = state === 'checked';
</script>

<div>
	<div
		class="flex items-center gap-3 justify-between text-xs w-full transition rounded-lg px-1 py-0.5 hover:bg-gray-50 dark:hover:bg-gray-850/50"
		style="padding-left: {level * 1.25}rem;"
	>
		<div class="flex items-center gap-1.5 w-full font-medium min-w-0">
			{#if hasChildren}
				<button
					type="button"
					class="p-0.5 -ml-0.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition shrink-0"
					on:click={() => toggleExpand(group.id)}
				>
					<div class="transition-transform {expanded ? 'rotate-90' : ''}">
						<ChevronRight className="size-3" strokeWidth="2.5" />
					</div>
				</button>
			{:else}
				<div class="w-4 shrink-0"></div>
			{/if}

			<Checkbox
				{state}
				indeterminate={state === 'indeterminate'}
				on:change={() => toggleGroup(group.id)}
			/>

			<button
				type="button"
				class="flex items-center gap-1.5 min-w-0 text-left"
				on:click={() => toggleGroup(group.id)}
			>
				<div class="shrink-0">
					<UserCircleSolid className="size-4" />
				</div>

				<div class="truncate">{group.name}</div>
			</button>

			{#if hasChildren && !expanded}
				<div class="text-[10px] text-gray-400 dark:text-gray-500 shrink-0">
					+{children.length} {$i18n.t('child groups')}
				</div>
			{/if}
		</div>

		<div class="flex justify-end items-center gap-0.5 shrink-0">
			{#if accessRoles.includes('write') && granted}
				<button
					type="button"
					on:click={() => onToggleWrite(group.id)}
				>
					{#if accessControl?.write?.group_ids?.includes(group.id)}
						<Badge type={'success'} content={$i18n.t('Write')} />
					{:else}
						<Badge type={'info'} content={$i18n.t('Read')} />
					{/if}
				</button>
			{/if}
		</div>
	</div>

	{#if hasChildren && expanded}
		<div class="mt-1 flex flex-col gap-1">
			{#each children as child (child.id)}
				<Self
					group={child}
					{groups}
					{childrenMap}
					{accessControl}
					{accessRoles}
					{expandedSet}
					{selectedClosure}
					{toggleExpand}
					{toggleGroup}
					{onToggleWrite}
					level={level + 1}
				/>
			{/each}
		</div>
	{/if}
</div>
