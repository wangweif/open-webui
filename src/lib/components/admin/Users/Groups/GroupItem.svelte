<script>
	import { toast } from 'svelte-sonner';
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	import { deleteGroupById, updateGroupById } from '$lib/apis/groups';

	import Pencil from '$lib/components/icons/Pencil.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import User from '$lib/components/icons/User.svelte';
	import UserCircleSolid from '$lib/components/icons/UserCircleSolid.svelte';
	import ChevronRight from '$lib/components/icons/ChevronRight.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import GroupModal from './EditGroupModal.svelte';
	import AddGroupModal from './AddGroupModal.svelte';
	import Self from './GroupItem.svelte';

	export let users = [];
	export let group = {
		name: 'Admins',
		user_ids: [1, 2, 3]
	};

	// parent_id -> 该父组的直属子组列表
	export let childrenMap = {};
	export let level = 0;

	export let setGroups = () => {};
	export let addGroupHandler = async () => {};

	let showEdit = false;
	let showAddSubGroup = false;
	let expanded = true;

	$: childGroups = childrenMap[group.id] ?? [];
	$: hasChildren = childGroups.length > 0;

	const updateHandler = async (_group) => {
		const res = await updateGroupById(localStorage.token, group.id, _group).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (res) {
			toast.success($i18n.t('Group updated successfully'));
			setGroups();
		}
	};

	const deleteHandler = async () => {
		const res = await deleteGroupById(localStorage.token, group.id).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (res) {
			toast.success($i18n.t('Group deleted successfully'));
			setGroups();
		}
	};
</script>

<GroupModal
	bind:show={showEdit}
	edit
	{users}
	{group}
	onSubmit={updateHandler}
	onDelete={deleteHandler}
/>

<AddGroupModal
	bind:show={showAddSubGroup}
	parentId={group.id}
	parentName={group.name}
	onSubmit={addGroupHandler}
/>

<div>
	<div class="flex items-center gap-3 justify-between px-1 text-xs w-full transition">
		<div
			class="flex items-center gap-1.5 w-full font-medium"
			style="padding-left: {level * 1.25}rem;"
		>
		{#if hasChildren}
			<button
				type="button"
				class="p-0.5 -ml-0.5 rounded hover:bg-gray-100 dark:hover:bg-gray-850 transition"
				on:click={() => {
					expanded = !expanded;
				}}
			>
				<div class="transition-transform {expanded ? 'rotate-90' : ''}">
					<ChevronRight className="size-3" strokeWidth="2.5" />
				</div>
			</button>
		{:else}
			<div class="w-4"></div>
		{/if}

		<button
			class="flex items-center gap-1.5 flex-1 text-left"
			on:click={() => {
				showEdit = true;
			}}
		>
			<div>
				<UserCircleSolid className="size-4" />
			</div>
			{group.name}
		</button>
	</div>

	<div class="flex items-center gap-1.5 w-full font-medium">
		{group.user_ids.length}

		<div>
			<User className="size-3.5" />
		</div>
	</div>

	<div class="w-full flex justify-end gap-1">
		<Tooltip content={$i18n.t('Add Sub Group')}>
			<button
				type="button"
				class=" rounded-lg p-1 hover:bg-gray-100 dark:hover:bg-gray-850 transition"
				on:click={() => {
					showAddSubGroup = true;
				}}
			>
				<Plus className="size-3.5" />
			</button>
		</Tooltip>

		<button
			type="button"
			class=" rounded-lg p-1 hover:bg-gray-100 dark:hover:bg-gray-850 transition"
			on:click={() => {
				showEdit = true;
			}}
		>
			<Pencil className="size-3.5" />
		</button>
	</div>
</div>

	{#if hasChildren && expanded}
		<div class="mt-2 flex flex-col gap-2">
			{#each childGroups as child (child.id)}
				<Self
					group={child}
					{users}
					{childrenMap}
					{setGroups}
					{addGroupHandler}
					level={level + 1}
				/>
			{/each}
		</div>
	{/if}
</div>
