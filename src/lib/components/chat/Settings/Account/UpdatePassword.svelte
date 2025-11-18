<script lang="ts">
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { updateUserPassword } from '$lib/apis/auths';
	import { validatePasswordStrength } from '$lib/utils';

	const i18n = getContext('i18n');

	let show = false;
	let currentPassword = '';
	let newPassword = '';
	let newPasswordConfirm = '';
	let passwordValidation: ReturnType<typeof validatePasswordStrength> | null = null;
	let showPasswordHint = false;

	const updatePasswordHandler = async () => {
		if (newPassword !== newPasswordConfirm) {
			toast.error(
				`The passwords you entered don't quite match. Please double-check and try again.`
			);
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

		const res = await updateUserPassword(localStorage.token, currentPassword, newPassword).catch(
			(error) => {
				toast.error(`${error}`);
				return null;
			}
		);

		if (res) {
			toast.success($i18n.t('Successfully updated.'));
			currentPassword = '';
			newPassword = '';
			newPasswordConfirm = '';
			passwordValidation = null;
			showPasswordHint = false;
		}
	};

	$: if (newPassword) {
		passwordValidation = validatePasswordStrength(newPassword);
		showPasswordHint = true;
	} else {
		passwordValidation = null;
		showPasswordHint = false;
	}
</script>

<form
	class="flex flex-col text-sm"
	on:submit|preventDefault={() => {
		updatePasswordHandler();
	}}
>
	<div class="flex justify-between items-center text-sm">
		<div class="  font-medium">{$i18n.t('Change Password')}</div>
		<button
			class=" text-xs font-medium text-gray-500"
			type="button"
			on:click={() => {
				show = !show;
			}}>{show ? $i18n.t('Hide') : $i18n.t('Show')}</button
		>
	</div>

	{#if show}
		<div class=" py-2.5 space-y-1.5">
			<div class="flex flex-col w-full">
				<div class=" mb-1 text-xs text-gray-500">{$i18n.t('Current Password')}</div>

				<div class="flex-1">
					<input
						class="w-full bg-transparent dark:text-gray-300 outline-hidden placeholder:opacity-30"
						type="password"
						bind:value={currentPassword}
						placeholder={$i18n.t('Enter your current password')}
						autocomplete="current-password"
						required
					/>
				</div>
			</div>

			<div class="flex flex-col w-full">
				<div class=" mb-1 text-xs text-gray-500">{$i18n.t('New Password')}</div>

				<div class="flex-1">
					<input
						class="w-full bg-transparent text-sm dark:text-gray-300 outline-hidden placeholder:opacity-30 border-b {passwordValidation && !passwordValidation.isValid ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'}"
						type="password"
						bind:value={newPassword}
						placeholder={$i18n.t('Enter your new password')}
						autocomplete="new-password"
						required
					/>
				</div>
				{#if showPasswordHint && passwordValidation}
					<div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
						<div class="mb-1">密码要求：</div>
						<div class="space-y-0.5">
							<div class="flex items-center">
								<span class="mr-2">{passwordValidation.strength.length ? '✓' : '✗'}</span>
								<span class={passwordValidation.strength.length ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>至少8位</span>
							</div>
							<div class="flex items-center">
								<span class="mr-2">{passwordValidation.strength.upper ? '✓' : '✗'}</span>
								<span class={passwordValidation.strength.upper ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>包含大写字母</span>
							</div>
							<div class="flex items-center">
								<span class="mr-2">{passwordValidation.strength.lower ? '✓' : '✗'}</span>
								<span class={passwordValidation.strength.lower ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>包含小写字母</span>
							</div>
							<div class="flex items-center">
								<span class="mr-2">{passwordValidation.strength.digit ? '✓' : '✗'}</span>
								<span class={passwordValidation.strength.digit ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>包含数字</span>
							</div>
							<div class="flex items-center">
								<span class="mr-2">{passwordValidation.strength.special ? '✓' : '✗'}</span>
								<span class={passwordValidation.strength.special ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>包含特殊字符</span>
							</div>
							<div class="flex items-center mt-1">
								<span class="mr-2">{passwordValidation.typeCount >= 3 ? '✓' : '✗'}</span>
								<span class={passwordValidation.typeCount >= 3 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>至少包含3种字符类型（当前：{passwordValidation.typeCount}种）</span>
							</div>
						</div>
					</div>
				{/if}
			</div>

			<div class="flex flex-col w-full">
				<div class=" mb-1 text-xs text-gray-500">{$i18n.t('Confirm Password')}</div>

				<div class="flex-1">
					<input
						class="w-full bg-transparent text-sm dark:text-gray-300 outline-hidden placeholder:opacity-30"
						type="password"
						bind:value={newPasswordConfirm}
						placeholder={$i18n.t('Confirm your new password')}
						autocomplete="off"
						required
					/>
				</div>
			</div>
		</div>

		<div class="mt-3 flex justify-end">
			<button
				class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
			>
				{$i18n.t('Update password')}
			</button>
		</div>
	{/if}
</form>
