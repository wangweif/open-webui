<script lang="ts">
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { updateUserPassword } from '$lib/apis/auths';
	import { validatePasswordStrength } from '$lib/utils';

	const i18n = getContext('i18n');

    export let show = false;
    export let token: string | null = null;
    export let onPasswordChanged: () => void = () => {};

	let currentPassword = '123456'; // 初始密码
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
					检测到您使用的是初始密码，为了账户安全，请立即更改密码。
				</p>
			</div>

			<form
				class="flex flex-col space-y-4"
				on:submit|preventDefault={() => {
					updatePasswordHandler();
				}}
			>
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

