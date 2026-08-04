<script lang="ts">
	import { getContext, onMount } from 'svelte';

	const i18n = getContext('i18n');

	import { getGroups } from '$lib/apis/groups';
	import AccessControlGroupItem from './AccessControlGroupItem.svelte';

	type Group = {
		id: string;
		name: string;
		parent_id?: string | null;
		user_ids?: string[];
		[Key: string]: any;
	};

	export let onChange: Function = () => {};

	export let accessRoles = ['read'];
	export let accessControl: any = {};

	export let allowPublic = true;

	let groups: Group[] = [];

	// parent_id -> 直属子组列表，用于树形展示
	let childrenMap: Record<string, Group[]> = {};
	// 顶级组（parent_id 为空）
	let rootGroups: Group[] = [];

	// 被授权组 id 闭包：用户显式选中的组 + 随父组一并授权的子孙组
	let selectedClosure: string[] = [];

	// 树中已展开的组（默认展开所有含子组的节点，便于浏览完整层级）
	let expandedGroupIds: string[] = [];

	const toggleExpand = (id: string) => {
		if (expandedGroupIds.includes(id)) {
			expandedGroupIds = expandedGroupIds.filter((gid) => gid !== id);
		} else {
			expandedGroupIds = [...expandedGroupIds, id];
		}
	};

	// 返回某组全部子孙 id
	const getDescendantIds = (id: string): string[] => {
		const result: string[] = [];
		const collect = (gid: string) => {
			const children = childrenMap[gid] ?? [];
			for (const child of children) {
				result.push(child.id);
				collect(child.id);
			}
		};
		collect(id);
		return result;
	};

	// 返回某组及其全部子孙 id
	const getSelfAndDescendantIds = (id: string): string[] => [id, ...getDescendantIds(id)];

	// 读取权限组 id 列表
	const getReadGroupIds = (): string[] => accessControl?.read?.group_ids ?? [];

	const getWriteGroupIds = (): string[] => accessControl?.write?.group_ids ?? [];

	// 切换某组的授权：
	// - 选中时，父组及其整棵子树一并授权（子组自动选中）
	// - 取消时，父组及其整棵子树一并撤销授权
	// 通过整体重建 accessControl 触发响应式更新
	const toggleGroup = (id: string) => {
		const ids = getSelfAndDescendantIds(id);
		if (getReadGroupIds().includes(id)) {
			accessControl = {
				...accessControl,
				read: {
					...accessControl.read,
					group_ids: getReadGroupIds().filter((gid) => !ids.includes(gid))
				},
				write: {
					...accessControl.write,
					group_ids: getWriteGroupIds().filter((gid) => !ids.includes(gid))
				}
			};
		} else {
			accessControl = {
				...accessControl,
				read: {
					...accessControl.read,
					group_ids: [...new Set([...getReadGroupIds(), ...ids])]
				}
			};
		}
	};

	const toggleWritePermission = (id: string) => {
		if (!accessRoles.includes('write')) return;
		accessControl = {
			...accessControl,
			write: {
				...accessControl.write,
				group_ids: getWriteGroupIds().includes(id)
					? getWriteGroupIds().filter((gid) => gid !== id)
					: [...getWriteGroupIds(), id]
			}
		};
	};

	$: if (!allowPublic && accessControl === null) {
		accessControl = {
			read: {
				group_ids: [],
				user_ids: []
			},
			write: {
				group_ids: [],
				user_ids: []
			}
		};
		onChange(accessControl);
	}

	onMount(async () => {
		groups = await getGroups(localStorage.token);

		childrenMap = {};
		for (const group of groups) {
			const pid = group.parent_id ?? '';
			if (pid) {
				if (!childrenMap[pid]) childrenMap[pid] = [];
				childrenMap[pid].push(group);
			}
		}
		rootGroups = groups.filter((group) => !(group.parent_id ?? ''));

		// 默认展开所有含子组的节点，完整展示层级结构
		expandedGroupIds = groups
			.filter((group) => (childrenMap[group.id] ?? []).length > 0)
			.map((group) => group.id);

		if (accessControl === null) {
			if (allowPublic) {
				accessControl = null;
			} else {
				accessControl = {
					read: {
						group_ids: [],
						user_ids: []
					},
					write: {
						group_ids: [],
						user_ids: []
					}
				};
				onChange(accessControl);
			}
		} else {
			accessControl = {
				read: {
					group_ids: accessControl?.read?.group_ids ?? [],
					user_ids: accessControl?.read?.user_ids ?? []
				},
				write: {
					group_ids: accessControl?.write?.group_ids ?? [],
					user_ids: accessControl?.write?.user_ids ?? []
				}
			};
		}
	});

	$: onChange(accessControl);

	// 已选闭包 = 显式授权组 + 随父组一并授权的子孙组
	$: selectedClosure = [
		...new Set(
			getReadGroupIds().flatMap((id) => getSelfAndDescendantIds(id))
		)
	];
</script>

<div class=" rounded-lg flex flex-col gap-2">
	<div class="">
		<div class=" text-sm font-semibold mb-1">{$i18n.t('Visibility')}</div>

		<div class="flex gap-2.5 items-center mb-1">
			<div>
				<div class=" p-2 bg-black/5 dark:bg-white/5 rounded-full">
					{#if accessControl !== null}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="1.5"
							stroke="currentColor"
							class="w-5 h-5"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
							/>
						</svg>
					{:else}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="1.5"
							stroke="currentColor"
							class="w-5 h-5"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M6.115 5.19l.319 1.913A6 6 0 008.11 10.36L9.75 12l-.387.775c-.217.433-.132.956.21 1.298l1.348 1.348c.21.21.329.497.329.795v1.089c0 .426.24.815.622 1.006l.153.076c.433.217.956.132 1.298-.21l.723-.723a8.7 8.7 0 002.288-4.042 1.087 1.087 0 00-.358-1.099l-1.33-1.108c-.251-.21-.582-.299-.905-.245l-1.17.195a1.125 1.125 0 01-.98-.314l-.295-.295a1.125 1.125 0 010-1.591l.13-.132a1.125 1.125 0 011.3-.21l.603.302a.809.809 0 001.086-1.086L14.25 7.5l1.256-.837a4.5 4.5 0 001.528-1.732l.146-.292M6.115 5.19A9 9 0 1017.18 4.64M6.115 5.19A8.965 8.965 0 0112 3c1.929 0 3.716.607 5.18 1.64"
							/>
						</svg>
					{/if}
				</div>
			</div>

			<div>
				<select
					id="models"
					class="outline-hidden bg-transparent text-sm font-medium rounded-lg block w-fit pr-10 max-w-full placeholder-gray-400"
					value={accessControl !== null ? 'private' : 'public'}
					on:change={(e) => {
						// @ts-ignore
						const target = e.target;
						if (target.value === 'public') {
							accessControl = null;
						} else {
							accessControl = {
								read: {
									group_ids: [],
									user_ids: []
								},
								write: {
									group_ids: [],
									user_ids: []
								}
							};
						}
					}}
				>
					<option class=" text-gray-700" value="private" selected>{$i18n.t('Private')}</option>
					{#if allowPublic}
						<option class=" text-gray-700" value="public" selected>{$i18n.t('Public')}</option>
					{/if}
				</select>


				<div class=" text-xs text-gray-400 font-medium">
					{#if accessControl !== null}
						{$i18n.t('Only select users and groups with permission can access')}
					{:else}
						{$i18n.t('Accessible to all users')}
					{/if}
				</div>
			</div>
		</div>
	</div>
	{#if accessControl !== null}
		<div>
			<div class="">
				<div class="flex justify-between mb-1.5">
					<div class="text-sm font-semibold">
						{$i18n.t('Groups')}
					</div>
					{#if selectedClosure.length > 0}
						<div class="text-xs text-gray-400 dark:text-gray-500 font-medium">
							{selectedClosure.length} {$i18n.t('groups granted')}
						</div>
					{/if}
				</div>

				<div class="text-xs text-gray-400 dark:text-gray-500 mb-2">
					{$i18n.t(
						'Selecting a parent group automatically selects all of its child groups'
					)}
				</div>

				<div class="flex flex-col gap-1 mb-1 px-0.5">
					{#if rootGroups.length > 0}
						{#each rootGroups as group (group.id)}
							<AccessControlGroupItem
								group={group}
								{groups}
								{childrenMap}
								{accessControl}
								{accessRoles}
								expandedSet={expandedGroupIds}
								{selectedClosure}
								{toggleExpand}
								{toggleGroup}
								onToggleWrite={toggleWritePermission}
							/>
						{/each}
					{:else}
						<div class="flex items-center justify-center">
							<div class="text-gray-500 text-xs text-center py-2 px-10">
								{$i18n.t('No groups with access, add a group to grant access')}
							</div>
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>
