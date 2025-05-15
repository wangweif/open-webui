<script lang="ts">
	import { getContext } from 'svelte';
	import { createEventDispatcher } from 'svelte';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	// 当前版本号
	const version = "v3.0";
</script>

<div class="flex flex-col h-full justify-between space-y-3 text-sm">
	<div class="space-y-3 overflow-y-scroll max-h-[28rem] lg:max-h-full">
		<div>
			<div class="mb-1.5 text-sm font-medium">{$i18n.t('Version')}</div>
			<div class="py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
				<div class="flex items-center">
					<span class="text-base font-medium">当前版本: {version}</span>
				</div>
			</div>
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