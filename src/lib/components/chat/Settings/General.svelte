<script lang="ts">
	import { onMount } from 'svelte';
	import { theme } from '$lib/stores';
	import { createEventDispatcher } from 'svelte';
	
	const dispatch = createEventDispatcher();

	// General
	let themes: string[] = ['dark', 'light'];
	let selectedTheme: string = localStorage.theme ?? 'light';

	onMount(async () => {
		selectedTheme = localStorage.theme ?? 'light';
		applyTheme(selectedTheme);
	});

	const applyTheme = (themeToApply: string) => {
		if (themeToApply === 'dark') {
			document.documentElement.style.setProperty('--color-gray-800', '#333');
			document.documentElement.style.setProperty('--color-gray-850', '#262626');
			document.documentElement.style.setProperty('--color-gray-900', '#171717');
			document.documentElement.style.setProperty('--color-gray-950', '#0d0d0d');
		}

		document.documentElement.classList.remove('dark', 'light');
		document.documentElement.classList.add(themeToApply);

		const metaThemeColor = document.querySelector('meta[name="theme-color"]');
		if (metaThemeColor) {
			metaThemeColor.setAttribute('content', themeToApply === 'dark' ? '#171717' : '#ffffff');
		}

		if (typeof window !== 'undefined' && window.applyTheme) {
			window.applyTheme();
		}
	};

	const themeChangeHandler = (newTheme: string) => {
		theme.set(newTheme);
		localStorage.setItem('theme', newTheme);
		applyTheme(newTheme);
	};
</script>

<div class="flex flex-col h-full justify-between text-sm">
	<div class="overflow-y-scroll max-h-[28rem] lg:max-h-full">
		<div class="">
			<div class="mb-1 text-sm font-medium">通用设置</div>

			<div class="flex w-full justify-between">
				<div class="self-center text-xs font-medium">主题</div>
				<div class="flex items-center relative">
					<select
						class="dark:bg-gray-900 w-fit pr-8 rounded-sm py-2 px-2 text-xs bg-transparent outline-hidden text-right"
						bind:value={selectedTheme}
						placeholder="选择主题"
						on:change={() => themeChangeHandler(selectedTheme)}
					>
						<option value="dark">🌑 深色</option>
						<option value="light">☀️ 浅色</option>
					</select>
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
			保存
		</button>
	</div>
</div>
