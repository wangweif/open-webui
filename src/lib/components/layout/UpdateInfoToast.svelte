<script lang="ts">
	import { getContext, createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	import { WEBUI_VERSION } from '$lib/constants';
	import XMark from '../icons/XMark.svelte';

	export let version = {
		current: WEBUI_VERSION,
		latest: WEBUI_VERSION
	};
</script>

<!-- <div
	class="flex items-start bg-primary-50 dark:bg-primary-950 border border-primary-500 dark:border-primary-800 text-primary-600 dark:text-primary-300 rounded-lg px-3.5 py-3 text-xs max-w-80 pr-2 w-full shadow-lg"
>
	<div class="flex-1 font-medium">
		{$i18n.t(`A new version (v{{LATEST_VERSION}}) is now available.`, {
			LATEST_VERSION: version.latest
		})}

		<a href="https://github.com/open-webui/open-webui/releases" target="_blank" class="underline">
			{$i18n.t('Update for the latest features and improvements.')}</a
		>
	</div>

	<div class=" shrink-0 pr-1">
		<button
			class=" hover:text-primary-900 dark:hover:text-primary-300 transition"
			on:click={() => {
				dispatch('close');
			}}
		>
			<XMark />
		</button>
	</div>
</div> -->
