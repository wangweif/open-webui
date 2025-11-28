<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { createEventDispatcher } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { getSecurityConfig, updateSecurityConfig } from '$lib/apis/auths';

	const i18n: any = getContext('i18n');
	const dispatch = createEventDispatcher();

	// 安全配置
	let jwtExpiresValue = '';
	let jwtExpiresUnit = 'm'; // 默认单位：分钟
	let passwordExpiresInDays = '';
	let loading = false;
	let saving = false;

	// 时间单位选项
	const timeUnits = [
		{ value: 'm', label: '分' },
		{ value: 'h', label: '时' },
		{ value: 'd', label: '日' },
		{ value: 'w', label: '周' }
	];

	// 解析JWT过期时间格式（如 "30m", "1h", "10d", "-1"）
	const parseJwtExpiresIn = (value: string) => {
		if (!value || value === '-1') {
			return { value: '-1', unit: 'm' };
		}
		
		// 匹配整数和单位（不再支持小数）
		const match = value.match(/^(-?\d+)([mhdw])$/);
		if (match) {
			return { value: match[1], unit: match[2] };
		}
		
		// 如果无法解析，返回默认值
		return { value: '', unit: 'm' };
	};

	// 组合JWT过期时间格式
	const combineJwtExpiresIn = (value: string, unit: string) => {
		if (value === '-1' || value === '') {
			return '-1';
		}
		return `${value}${unit}`;
	};

	// 加载安全配置
	const loadSecurityConfig = async () => {
		loading = true;
		try {
			const config = await getSecurityConfig(localStorage.token);
			if (config) {
				const parsed = parseJwtExpiresIn(config.JWT_EXPIRES_IN || '');
				jwtExpiresValue = parsed.value;
				jwtExpiresUnit = parsed.unit;
				passwordExpiresInDays = String(config.PASSWORD_EXPIRES_IN_DAYS || '90');
			}
		} catch (error) {
			console.error('Failed to load security config:', error);
			toast.error('加载安全配置失败');
		} finally {
			loading = false;
		}
	};

	// 保存安全配置
	const saveSecurityConfig = async () => {
		// 验证JWT过期时间
		if (jwtExpiresValue !== '-1') {
			// 检查是否为整数
			if (!jwtExpiresValue || !/^-?\d+$/.test(jwtExpiresValue)) {
				toast.error('JWT过期时间必须是整数或-1（永不过期）');
				return;
			}
			// 检查是否大于0
			const numValue = parseInt(jwtExpiresValue);
			if (isNaN(numValue) || numValue <= 0) {
				toast.error('JWT过期时间必须是大于0的整数或-1（永不过期）');
				return;
			}
		}

		// 验证密码过期天数
		const days = parseInt(passwordExpiresInDays);
		if (isNaN(days) || days <= 0) {
			toast.error('密码过期天数必须是大于0的数字');
			return;
		}

		saving = true;
		try {
			const jwtExpiresIn = combineJwtExpiresIn(jwtExpiresValue, jwtExpiresUnit);
			await updateSecurityConfig(localStorage.token, {
				JWT_EXPIRES_IN: jwtExpiresIn,
				PASSWORD_EXPIRES_IN_DAYS: String(passwordExpiresInDays)
			});
			toast.success('安全配置保存成功');
			dispatch('save');
		} catch (error) {
			console.error('Failed to save security config:', error);
			toast.error('保存安全配置失败');
		} finally {
			saving = false;
		}
	};

	onMount(loadSecurityConfig);
</script>

<div class="flex flex-col h-full justify-between space-y-3 text-sm">
	<div class="space-y-3 overflow-y-scroll max-h-[28rem] lg:max-h-full">
		{#if loading}
			<div class="py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
				<span class="text-sm text-gray-600 dark:text-gray-400">加载中...</span>
			</div>
		{:else}
			<!-- JWT过期时间设置 -->
			<div>
				<div class="mb-1.5 text-sm font-medium">JWT过期时间</div>
				<div class="py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
					<div class="flex gap-2">
						<input
							class="flex-1 rounded-lg py-2 px-4 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 outline-hidden"
							type="number"
							min="-1"
							step="1"
							placeholder="输入整数，-1表示永不过期"
							bind:value={jwtExpiresValue}
							disabled={jwtExpiresValue === '-1'}
							on:keydown={(e) => {
								// 阻止输入小数点、e、E、+、-（除了开头的-）
								if (e.key === '.' || e.key === 'e' || e.key === 'E' || e.key === '+' || 
								    (e.key === '-' && e.currentTarget.selectionStart !== 0)) {
									e.preventDefault();
								}
							}}
							on:input={(e) => {
								const value = e.currentTarget.value;
								// 禁止输入小数，只允许整数或-1
								if (value && value !== '-1' && (value.includes('.') || value.includes('e') || value.includes('E'))) {
									// 移除所有非整数字符（保留-1）
									const cleaned = value.replace(/[^\d-]/g, '').replace(/(?!^)-/g, '');
									e.currentTarget.value = cleaned;
									jwtExpiresValue = cleaned;
								}
							}}
						/>
						<select
							class="w-24 rounded-lg py-2 px-3 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 outline-hidden"
							bind:value={jwtExpiresUnit}
							disabled={jwtExpiresValue === '-1'}
						>
							{#each timeUnits as unit}
								<option value={unit.value}>{unit.label}</option>
							{/each}
						</select>
					</div>
					<div class="mt-2 flex items-center gap-2">
						<label class="flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
							<input
								type="checkbox"
								checked={jwtExpiresValue === '-1'}
								on:change={(e) => {
									const target = e.currentTarget;
									jwtExpiresValue = target.checked ? '-1' : '30';
								}}
								class="rounded"
							/>
							<span>永不过期</span>
						</label>
					</div>
				</div>
			</div>

			<!-- 密码过期时间设置 -->
			<div>
				<div class="mb-1.5 text-sm font-medium">密码过期时间（天）</div>
				<div class="py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
					<input
						class="w-full rounded-lg py-2 px-4 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 outline-hidden"
						type="number"
						min="1"
						placeholder="例如: 90"
						bind:value={passwordExpiresInDays}
					/>
					<div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
						密码过期天数，必须大于0
					</div>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full disabled:opacity-50 disabled:cursor-not-allowed"
			on:click={saveSecurityConfig}
			disabled={saving || loading}
		>
			{saving ? '保存中...' : $i18n.t('Save')}
		</button>
	</div>
</div>

