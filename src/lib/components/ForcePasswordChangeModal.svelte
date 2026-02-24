<script lang="ts">
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { updateUserPassword } from '$lib/apis/auths';
	import { validatePasswordStrength } from '$lib/utils';

	const i18n = getContext('i18n');

    export let show = false;
    export let token: string | null = null;
    export let onPasswordChanged: () => void = () => {};

	let currentPassword = ''; // 当前密码，用户需要输入
	let showCurrentPassword = false;
	let newPassword = '';
	let newPasswordConfirm = '';
	let passwordValidation: ReturnType<typeof validatePasswordStrength> | null = null;
	let showPasswordHint = false;
	let isSubmitting = false;

	const updatePasswordHandler = async () => {
		if (!token) {
			toast.error('缺少认证信息，请重新登录。');
			return;
		}
		if (newPassword !== newPasswordConfirm) {
			toast.error('两次输入的密码不一致，请重新输入。');
			newPassword = '';
			newPasswordConfirm = '';
			return;
		}

		// 验证密码强度
		const validation = validatePasswordStrength(newPassword);
		if (!validation.isValid) {
			toast.error(validation.errors.join('；'));
			return;
		}

		isSubmitting = true;
		const res = await updateUserPassword(token, currentPassword, newPassword).catch(
			(error) => {
				toast.error(`${error}`);
				isSubmitting = false;
				return null;
			}
		);

		if (res) {
			toast.success('密码已成功更改！');
			show = false;
			currentPassword = '';
			newPassword = '';
			newPasswordConfirm = '';
			passwordValidation = null;
			showPasswordHint = false;
			onPasswordChanged();
		}
		isSubmitting = false;
	};

	$: if (newPassword) {
		passwordValidation = validatePasswordStrength(newPassword);
		showPasswordHint = true;
	} else {
		passwordValidation = null;
		showPasswordHint = false;
	}
</script>

{#if show}
	<div
		class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm"
		on:click|self={() => {}}
		role="dialog"
		aria-modal="true"
		aria-labelledby="force-password-change-title"
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 border border-gray-200 dark:border-gray-700"
		>
			<div class="mb-6">
				<h2 id="force-password-change-title" class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
					需要更改密码
				</h2>
				<p class="text-sm text-gray-600 dark:text-gray-400">
					您的密码已过期，为了账户安全，请立即更改密码。
				</p>
			</div>

			<form
				class="flex flex-col space-y-4"
				on:submit|preventDefault={() => {
					updatePasswordHandler();
				}}
			>
				<div class="flex flex-col">
					<label for="current-password-input" class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						当前密码
					</label>
					<div class="relative">
						{#if showCurrentPassword}
							<input
								id="current-password-input"
								class="w-full bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg py-2.5 px-3 pr-10 focus:outline-none focus:border-2 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20 text-gray-900 dark:text-gray-100"
								type="text"
								bind:value={currentPassword}
								placeholder="请输入当前密码"
								autocomplete="current-password"
								required
								disabled={isSubmitting}
							/>
						{:else}
							<input
								id="current-password-input"
								class="w-full bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg py-2.5 px-3 pr-10 focus:outline-none focus:border-2 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20 text-gray-900 dark:text-gray-100"
								type="password"
								bind:value={currentPassword}
								placeholder="请输入当前密码"
								autocomplete="current-password"
								required
								disabled={isSubmitting}
							/>
						{/if}
						<button
							type="button"
							class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
							on:click={() => showCurrentPassword = !showCurrentPassword}
						>
							{#if showCurrentPassword}
								<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"></path>
								</svg>
							{:else}
								<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
								</svg>
							{/if}
						</button>
					</div>
				</div>
				<div class="flex flex-col">
					<label for="new-password-input" class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						新密码
					</label>
					<input
						id="new-password-input"
						class="w-full bg-transparent border {passwordValidation && !passwordValidation.isValid ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-lg py-2.5 px-3 focus:outline-none focus:border-2 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20 text-gray-900 dark:text-gray-100"
						type="password"
						bind:value={newPassword}
						placeholder="请输入新密码"
						autocomplete="new-password"
						required
						disabled={isSubmitting}
						style="-webkit-text-security: disc; text-security: disc;"
					/>
					{#if showPasswordHint && passwordValidation}
						<div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
							<div class="mb-1">密码要求：</div>
							<div class="space-y-0.5">
								<div class="flex items-center">
									<span class="mr-2">{passwordValidation.strength.length ? '✓' : '✗'}</span>
									<span
										class={passwordValidation.strength.length
											? 'text-green-600 dark:text-green-400'
											: 'text-red-600 dark:text-red-400'}>至少8位</span
									>
								</div>
								<div class="flex items-center">
									<span class="mr-2">{passwordValidation.strength.upper ? '✓' : '✗'}</span>
									<span
										class={passwordValidation.strength.upper
											? 'text-green-600 dark:text-green-400'
											: 'text-gray-500 dark:text-gray-400'}>包含大写字母</span
									>
								</div>
								<div class="flex items-center">
									<span class="mr-2">{passwordValidation.strength.lower ? '✓' : '✗'}</span>
									<span
										class={passwordValidation.strength.lower
											? 'text-green-600 dark:text-green-400'
											: 'text-gray-500 dark:text-gray-400'}>包含小写字母</span
									>
								</div>
								<div class="flex items-center">
									<span class="mr-2">{passwordValidation.strength.digit ? '✓' : '✗'}</span>
									<span
										class={passwordValidation.strength.digit
											? 'text-green-600 dark:text-green-400'
											: 'text-gray-500 dark:text-gray-400'}>包含数字</span
									>
								</div>
								<div class="flex items-center">
									<span class="mr-2">{passwordValidation.strength.special ? '✓' : '✗'}</span>
									<span
										class={passwordValidation.strength.special
											? 'text-green-600 dark:text-green-400'
											: 'text-gray-500 dark:text-gray-400'}>包含特殊字符</span
									>
								</div>
								<div class="flex items-center mt-1">
									<span class="mr-2">{passwordValidation.typeCount >= 3 ? '✓' : '✗'}</span>
									<span
										class={passwordValidation.typeCount >= 3
											? 'text-green-600 dark:text-green-400'
											: 'text-red-600 dark:text-red-400'}>至少包含3种字符类型（当前：{passwordValidation.typeCount}种）</span
									>
								</div>
							</div>
						</div>
					{/if}
				</div>

				<div class="flex flex-col">
					<label for="confirm-password-input" class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						确认新密码
					</label>
					<input
						id="confirm-password-input"
						class="w-full bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg py-2.5 px-3 focus:outline-none focus:border-2 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20 text-gray-900 dark:text-gray-100"
						type="password"
						bind:value={newPasswordConfirm}
						placeholder="请再次输入新密码"
						autocomplete="off"
						required
						disabled={isSubmitting}
						style="-webkit-text-security: disc; text-security: disc;"
					/>
				</div>

				<div class="flex justify-end space-x-3 pt-4">
					<button
						class="px-6 py-2.5 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white transition rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
						type="submit"
						disabled={isSubmitting}
					>
						{isSubmitting ? '更改中...' : '更改密码'}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

