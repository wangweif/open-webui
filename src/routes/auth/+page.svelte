<script>
	import { toast } from 'svelte-sonner';

	import { onMount, getContext, tick } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	import { getBackendConfig } from '$lib/apis';
	import { ldapUserSignIn, getSessionUser, userSignIn, userSignUp } from '$lib/apis/auths';

	import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';
	import { WEBUI_NAME, config, user, socket } from '$lib/stores';

	import { generateInitialsImage, canvasPixelTest, validatePasswordStrength } from '$lib/utils';

	import Spinner from '$lib/components/common/Spinner.svelte';
	import OnBoarding from '$lib/components/OnBoarding.svelte';

	const i18n = getContext('i18n');

	let loaded = false;

	let mode = $config?.features.enable_ldap ? 'ldap' : 'signin';

	let name = '';
	let email = '';
	let password = '';
	let showPassword = false;
	let passwordValidation = null;
	let showPasswordHint = false;

	let ldapUsername = '';

	const togglePasswordVisibility = () => {
		showPassword = !showPassword;
	};

	const querystringValue = (key) => {
		const querystring = window.location.search;
		const urlParams = new URLSearchParams(querystring);
		return urlParams.get(key);
	};

	const setSessionUser = async (sessionUser) => {
		if (sessionUser) {
			console.log(sessionUser);
			toast.success($i18n.t(`You're now logged in.`));
			if (sessionUser.token) {
				localStorage.token = sessionUser.token;
			}

			$socket.emit('user-join', { auth: { token: sessionUser.token } });
			await user.set(sessionUser);
			await config.set(await getBackendConfig());

			const redirectPath = querystringValue('redirect') || '/';
			goto(redirectPath);
		}
	};

	const signInHandler = async () => {
		const sessionUser = await userSignIn(email, password).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		await setSessionUser(sessionUser);
	};

	const signUpHandler = async () => {
		// 验证密码强度
		const validation = validatePasswordStrength(password);
		if (!validation.isValid) {
			toast.error(validation.errors.join('；'));
			return;
		}

		const sessionUser = await userSignUp(name, email, password, generateInitialsImage(name)).catch(
			(error) => {
				toast.error(`${error}`);
				return null;
			}
		);

		await setSessionUser(sessionUser);
	};

	$: if (password) {
		passwordValidation = validatePasswordStrength(password);
		showPasswordHint = true;
	} else {
		passwordValidation = null;
		showPasswordHint = false;
	}

	const ldapSignInHandler = async () => {
		const sessionUser = await ldapUserSignIn(ldapUsername, password).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		await setSessionUser(sessionUser);
	};
    const guestSignInHandler = async () => {
        const guestEmail = 'guest@bjzntd.com';
        const guestPassword = '123456';

        const sessionUser = await userSignIn(guestEmail, guestPassword).catch((error) => {
            toast.error(`${error}`);
            return null;
        });

        await setSessionUser(sessionUser);
    };

	const submitHandler = async () => {
		if (mode === 'ldap') {
			await ldapSignInHandler();
		} else if (mode === 'signin') {
			await signInHandler();
		} else {
			await signUpHandler();
		}
	};

	const checkOauthCallback = async () => {
		if (!$page.url.hash) {
			return;
		}
		const hash = $page.url.hash.substring(1);
		if (!hash) {
			return;
		}
		const params = new URLSearchParams(hash);
		const token = params.get('token');
		if (!token) {
			return;
		}
		const sessionUser = await getSessionUser(token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		if (!sessionUser) {
			return;
		}
		localStorage.token = token;
		await setSessionUser(sessionUser);
	};

	let onboarding = false;

	async function setLogoImage() {
		await tick();
		const logo = document.getElementById('logo');

		if (logo) {
			const isDarkMode = document.documentElement.classList.contains('dark');

			if (isDarkMode) {
				const darkImage = new Image();
				darkImage.src = '/static/favicon-dark.png';

				darkImage.onload = () => {
					logo.src = '/static/favicon-dark.png';
					logo.style.filter = ''; // Ensure no inversion is applied if favicon-dark.png exists
				};

				darkImage.onerror = () => {
					logo.style.filter = 'invert(1)'; // Invert image if favicon-dark.png is missing
				};
			}
		}
	}

	onMount(async () => {
		if ($user !== undefined) {
			const redirectPath = querystringValue('redirect') || '/';
			goto(redirectPath);
		}
		await checkOauthCallback();

		loaded = true;
		setLogoImage();

		if (($config?.features.auth_trusted_header ?? false) || $config?.features.auth === false) {
			await signInHandler();
		} else {
			onboarding = $config?.onboarding ?? false;
		}
	});
</script>

<svelte:head>
	<title>
		{`${$WEBUI_NAME}`}
	</title>
</svelte:head>

<OnBoarding
	bind:show={onboarding}
	getStartedHandler={() => {
		onboarding = false;
		mode = $config?.features.enable_ldap ? 'ldap' : 'signup';
	}}
/>

<div class="w-full h-screen max-h-[100dvh] text-white relative">
	<div class="w-full h-full absolute top-0 left-0 bg-white dark:bg-black"></div>

	<div class="w-full absolute top-0 left-0 right-0 h-8 drag-region" />

	{#if loaded}
		<div class="fixed m-10 z-50">
			<div class="flex space-x-2">
				<div class=" self-center">
					<!--
					<img
						id="logo"
						crossorigin="anonymous"
						src="{WEBUI_BASE_URL}/static/splash.png"
						class=" w-6 rounded-full"
						alt="logo"
					/>
					-->
				</div>
			</div>
		</div>

		<div
			class="fixed top-50 bg-transparent min-h-screen w-full flex justify-center font-primary z-50 text-black dark:text-white"
		>
			<div class="w-full sm:max-w-md px-10 min-h-screen flex flex-col text-center">
				{#if ($config?.features.auth_trusted_header ?? false) || $config?.features.auth === false}
					<div class=" my-auto pb-10 w-full">
						<div
							class="flex items-center justify-center gap-3 text-xl sm:text-2xl text-center font-semibold dark:text-gray-200"
						>
							<div>
								{$i18n.t('Signing in to {{WEBUI_NAME}}', { WEBUI_NAME: $WEBUI_NAME })}
							</div>

							<div>
								<Spinner />
							</div>
						</div>
					</div>
				{:else}
					<div class="mt-5 pb-10 w-full dark:text-gray-100">
						<div class="mb-8 flex items-center justify-center">
							<!-- <div class="flex-shrink-0">
								<img
									src="/login.jpg"
									alt="农科小智"
									class="w-40 h-40 object-contain"
								/>
							</div> -->
							<!-- <div class="ml-4">
								<div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
									农科小智
								</div>
							</div> -->
						</div>

						<!-- 登录表单区域，添加圆角矩形框 -->
						<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 border border-gray-200 dark:border-gray-700">
							<form
								class="flex flex-col justify-center"
								on:submit={(e) => {
									e.preventDefault();
									submitHandler();
								}}
							>
								<div class="mb-2">
									<div class="text-3xl font-medium">
										{#if $config?.onboarding ?? false}
											{$i18n.t(`开始使用`)}
										{:else if mode === 'ldap'}
											{$i18n.t(`登录 with LDAP`)}
										{:else if mode === 'signin'}
											{$i18n.t(`登录`)}
										{:else}
											{$i18n.t(`注册`)}
										{/if}
									</div>

									{#if $config?.onboarding ?? false}
										<div class="mt-3 text-base font-medium text-gray-500">
											ⓘ
											{$i18n.t(
												'does not make any external connections, and your data stays securely on your locally hosted server.'
											)}
										</div>
									{/if}
								</div>

								{#if $config?.features.enable_login_form || $config?.features.enable_ldap}
									<div class="flex flex-col mt-6">
										{#if mode === 'signup'}
											<div class="mb-4 flex items-center">
												<!--<div class="text-base font-medium text-left mb-2">{$i18n.t('Name')}</div>-->
                                                <label class="text-base font-medium mr-4">{$i18n.t('Name')}</label>
												<div class="relative">
													<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
														<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
														</svg>
													</div>
													<input
														bind:value={name}
														type="text"
														class="w-full text-base bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg py-3 pl-10 pr-4 focus:outline-none focus:border-2 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20 focus:shadow-lg"
														autocomplete="name"
														placeholder={$i18n.t('Enter Your Full Name')}
														required
													/>
												</div>
											</div>
										{/if}

										{#if mode === 'ldap'}
											<div class="mb-4">
												<div class="text-base font-medium text-left mb-2">{$i18n.t('Username')}</div>
												<div class="relative">
													<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
														<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
														</svg>
													</div>
													<input
														bind:value={ldapUsername}
														type="text"
														class="w-full text-base bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg py-3 pl-10 pr-4 focus:outline-none focus:border-2 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20 focus:shadow-lg"
														autocomplete="username"
														name="username"
														placeholder={$i18n.t('Enter Your Username')}
														required
													/>
												</div>
											</div>
										{:else}
											<div class="mb-4 flex items-center">
												<!--<div class="text-base font-medium text-left mb-2">{$i18n.t('Email')}</div>-->
                                                <label class="text-base font-medium mr-4">邮箱</label>
												<div class="relative">
													<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
														<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 7.89a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
														</svg>
													</div>
													<input
														bind:value={email}
														type="email"
														class="w-full text-base bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg py-3 pl-10 pr-4 focus:outline-none focus:border-2 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20 focus:shadow-lg"
														autocomplete="email"
														name="email"
														placeholder="请输入邮箱地址"
														required
													/>
												</div>
											</div>
										{/if}

										<div class="mb-4 flex items-center">
											<!--<div class="text-base font-medium text-left mb-2">密码</div>-->
                                            <label class="text-base font-medium mr-4">密码</label>
											<div class="relative">
												<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
													<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
													</svg>
												</div>
												{#if showPassword}
													<input
														bind:value={password}
														type="text"
														class="w-full text-base bg-transparent border {passwordValidation && !passwordValidation.isValid ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-lg py-3 pl-10 pr-4 focus:outline-none focus:border-2 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20 focus:shadow-lg"
														placeholder="请输入密码"
														autocomplete={mode === 'signup' ? 'new-password' : 'current-password'}
														name={mode === 'signup' ? 'new-password' : 'current-password'}
														required
													/>
												{:else}
													<input
														bind:value={password}
														type="password"
														class="w-full text-base bg-transparent border {passwordValidation && !passwordValidation.isValid ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-lg py-3 pl-10 pr-4 focus:outline-none focus:border-2 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20 focus:shadow-lg"
														placeholder="请输入密码"
														autocomplete={mode === 'signup' ? 'new-password' : 'current-password'}
														name={mode === 'signup' ? 'new-password' : 'current-password'}
														required
													/>
												{/if}
												<div class="absolute inset-y-0 right-0 pr-3 flex items-center">
													<button type="button" on:click={togglePasswordVisibility} class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none">
														{#if showPassword}
															<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18"></path>
															</svg>
														{:else}
															<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
																<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
															</svg>
														{/if}
													</button>
												</div>
											</div>
										</div>
										{#if mode === 'signup' && showPasswordHint && passwordValidation}
											<div class="mb-4 text-xs text-gray-500 dark:text-gray-400">
												<div class="mb-2">密码要求：</div>
												<div class="space-y-1">
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
													<div class="flex items-center mt-2">
														<span class="mr-2">{passwordValidation.typeCount >= 3 ? '✓' : '✗'}</span>
														<span class={passwordValidation.typeCount >= 3 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>至少包含3种字符类型（当前：{passwordValidation.typeCount}种）</span>
													</div>
												</div>
											</div>
										{/if}
									</div>
								{/if}

								<div class="mt-6">
									{#if $config?.features.enable_login_form || $config?.features.enable_ldap}
										{#if mode === 'ldap'}
											<button
												class="bg-primary-500 hover:bg-primary-600 text-white transition w-full rounded-full font-medium text-base py-3"
												type="submit"
											>
												{$i18n.t('Authenticate')}
											</button>

										{:else}
											<button
												class="bg-primary-500 hover:bg-primary-600 text-white transition w-full rounded-full font-medium text-base py-3"
												type="submit"
											>
												{mode === 'signin'
													? $i18n.t('立即登录')
													: ($config?.onboarding ?? false)
														? $i18n.t('Create Admin Account')
														: $i18n.t('Create Account')}
											</button>

                                            {#if $config?.features.enable_signup && !($config?.onboarding ?? false)}
												<div class="mt-6 text-base text-center">


													<button
														class="font-medium underline"
														type="button"
														on:click={() => {
															if (mode === 'signin') {
																mode = 'signup';
															} else {
																mode = 'signin';
															}
														}}
													>
														{mode === 'signin' ? $i18n.t('Sign up') : $i18n.t('Sign in')}
													</button>
													{#if mode === 'signin'}
														<span class="mx-2">|</span>
														<button
																class="font-medium underline"
																type="button"
																on:click={guestSignInHandler}
														>
															{$i18n.t('游客登录')}
														</button>
													{/if}
												</div>
											{/if}
										{/if}
									{/if}
								</div>
							</form>

							{#if Object.keys($config?.oauth?.providers ?? {}).length > 0}
								<div class="inline-flex items-center justify-center w-full">
									<hr class="w-32 h-px my-6 border-0 dark:bg-gray-100/10 bg-gray-700/10" />
									{#if $config?.features.enable_login_form || $config?.features.enable_ldap}
										<span
											class="px-3 text-base font-medium text-gray-900 dark:text-white bg-transparent"
											>{$i18n.t('or')}</span
										>
									{/if}
									<hr class="w-32 h-px my-6 border-0 dark:bg-gray-100/10 bg-gray-700/10" />
								</div>
								<div class="flex flex-col space-y-3">
									{#if $config?.oauth?.providers?.google}
										<button
											class="flex justify-center items-center bg-primary-500 hover:bg-primary-600 text-white transition w-full rounded-full font-medium text-base py-3"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/google/login`;
											}}
										>
											<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" class="size-6 mr-3">
												<path
													fill="#EA4335"
													d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
												/><path
													fill="#4285F4"
													d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
												/><path
													fill="#FBBC05"
													d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
												/><path
													fill="#34A853"
													d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
												/><path fill="none" d="M0 0h48v48H0z" />
											</svg>
											<span>{$i18n.t('Continue with {{provider}}', { provider: 'Google' })}</span>
										</button>
									{/if}
									{#if $config?.oauth?.providers?.microsoft}
										<button
											class="flex justify-center items-center bg-primary-500 hover:bg-primary-600 text-white transition w-full rounded-full font-medium text-base py-3"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/microsoft/login`;
											}}
										>
											<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 21 21" class="size-6 mr-3">
												<rect x="1" y="1" width="9" height="9" fill="#f25022" /><rect
													x="1"
													y="11"
													width="9"
													height="9"
													fill="#00a4ef"
												/><rect x="11" y="1" width="9" height="9" fill="#7fba00" /><rect
													x="11"
													y="11"
													width="9"
													height="9"
													fill="#ffb900"
												/>
											</svg>
											<span>{$i18n.t('Continue with {{provider}}', { provider: 'Microsoft' })}</span>
										</button>
									{/if}
									{#if $config?.oauth?.providers?.github}
										<button
											class="flex justify-center items-center bg-primary-500 hover:bg-primary-600 text-white transition w-full rounded-full font-medium text-base py-3"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/github/login`;
											}}
										>
											<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="size-6 mr-3">
												<path
													fill="currentColor"
													d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.92 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57C20.565 21.795 24 17.31 24 12c0-6.63-5.37-12-12-12z"
												/>
											</svg>
											<span>{$i18n.t('Continue with {{provider}}', { provider: 'GitHub' })}</span>
										</button>
									{/if}
									{#if $config?.oauth?.providers?.oidc}
										<button
											class="flex justify-center items-center bg-primary-500 hover:bg-primary-600 text-white transition w-full rounded-full font-medium text-base py-3"
											on:click={() => {
												window.location.href = `${WEBUI_BASE_URL}/oauth/oidc/login`;
											}}
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												fill="none"
												viewBox="0 0 24 24"
												stroke-width="1.5"
												stroke="currentColor"
												class="size-6 mr-3"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z"
												/>
											</svg>

											<span
												>{$i18n.t('Continue with {{provider}}', {
													provider: $config?.oauth?.providers?.oidc ?? 'SSO'
												})}</span
											>
										</button>
									{/if}
								</div>
							{/if}

							{#if $config?.features.enable_ldap && $config?.features.enable_login_form}
								<div class="mt-4">
									<button
										class="flex justify-center items-center text-sm w-full text-center underline"
										type="button"
										on:click={() => {
											if (mode === 'ldap')
												mode = ($config?.onboarding ?? false) ? 'signup' : 'signin';
											else mode = 'ldap';
										}}
									>
										<span
											>{mode === 'ldap'
												? $i18n.t('Continue with Email')
												: $i18n.t('Continue with LDAP')}</span
										>
									</button>
								</div>
							{/if}
						</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
