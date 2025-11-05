<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, tick, getContext, onMount, onDestroy } from 'svelte';
	import { config, settings } from '$lib/stores';
	import { blobToFile, calculateSHA256, extractCurlyBraceWords } from '$lib/utils';

	import { transcribeAudio } from '$lib/apis/audio';

	const i18n = getContext('i18n');

	const dispatch = createEventDispatcher();

	export let recording = false;
	export let className = ' p-2.5 w-full max-w-full';
	export let showPressToTalk = false;
	export let isPressingVoice = false;

	let loading = false;
	let confirmed = false;

	let durationSeconds = 0;
	let durationCounter = null;

	let transcription = '';

	const startDurationCounter = () => {
		durationCounter = setInterval(() => {
			durationSeconds++;
		}, 1000);
	};

	const stopDurationCounter = () => {
		clearInterval(durationCounter);
		durationSeconds = 0;
	};

	$: if ((recording && !showPressToTalk) || (showPressToTalk && isPressingVoice && recording)) {
		startRecording();
	} else {
		stopRecording();
	}

	// 监听按压式语音输入
	$: if (showPressToTalk && isPressingVoice && !recording) {
		recording = true;
	} 

	const formatSeconds = (seconds) => {
		const minutes = Math.floor(seconds / 60);
		const remainingSeconds = seconds % 60;
		const formattedSeconds = remainingSeconds < 10 ? `0${remainingSeconds}` : remainingSeconds;
		return `${minutes}:${formattedSeconds}`;
	};

	let stream;
	let speechRecognition;

	let mediaRecorder;
	let audioChunks = [];

	const MIN_DECIBELS = -45;
	let VISUALIZER_BUFFER_LENGTH = 300;

	let visualizerData = Array(VISUALIZER_BUFFER_LENGTH).fill(0);
	let pressStartY = 0; // 记录按下时的Y坐标
	let currentY = 0; // 记录当前的Y坐标
	let isCancelGesture = false; // 是否触发了取消手势
	const CANCEL_THRESHOLD = 80; // 上滑多少像素取消（可调整）
	let pressStartTime = 0; // 记录按下时的时间戳
	const MIN_PRESS_DURATION = 300; // 最小按压时长（毫秒）

	// Function to calculate the RMS level from time domain data
	const calculateRMS = (data: Uint8Array) => {
		let sumSquares = 0;
		for (let i = 0; i < data.length; i++) {
			const normalizedValue = (data[i] - 128) / 128; // Normalize the data
			sumSquares += normalizedValue * normalizedValue;
		}
		return Math.sqrt(sumSquares / data.length);
	};

	const normalizeRMS = (rms) => {
		rms = rms * 10;
		const exp = 1.5; // Adjust exponent value; values greater than 1 expand larger numbers more and compress smaller numbers more
		const scaledRMS = Math.pow(rms, exp);

		// Scale between 0.01 (1%) and 1.0 (100%)
		return Math.min(1.0, Math.max(0.01, scaledRMS));
	};

	const analyseAudio = (stream) => {
		const audioContext = new AudioContext();
		const audioStreamSource = audioContext.createMediaStreamSource(stream);

		const analyser = audioContext.createAnalyser();
		analyser.minDecibels = MIN_DECIBELS;
		audioStreamSource.connect(analyser);

		const bufferLength = analyser.frequencyBinCount;

		const domainData = new Uint8Array(bufferLength);
		const timeDomainData = new Uint8Array(analyser.fftSize);

		let lastSoundTime = Date.now();

		const detectSound = () => {
			const processFrame = () => {
				if (!recording || loading) return;

				if (recording && !loading) {
					analyser.getByteTimeDomainData(timeDomainData);
					analyser.getByteFrequencyData(domainData);

					// Calculate RMS level from time domain data
					const rmsLevel = calculateRMS(timeDomainData);
					// Push the calculated decibel level to visualizerData
					visualizerData.push(normalizeRMS(rmsLevel));

					// Ensure visualizerData array stays within the buffer length
					if (visualizerData.length >= VISUALIZER_BUFFER_LENGTH) {
						visualizerData.shift();
					}

					visualizerData = visualizerData;

					// if (domainData.some((value) => value > 0)) {
					// 	lastSoundTime = Date.now();
					// }

					// if (recording && Date.now() - lastSoundTime > 3000) {
					// 	if ($settings?.speechAutoSend ?? false) {
					// 		confirmRecording();
					// 	}
					// }
				}

				window.requestAnimationFrame(processFrame);
			};

			window.requestAnimationFrame(processFrame);
		};

		detectSound();
	};

	const transcribeHandler = async (audioBlob) => {
		// Create a blob from the audio chunks

		await tick();
		const file = blobToFile(audioBlob, 'recording.wav');

		const res = await transcribeAudio(localStorage.token, file).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (res) {
			console.log(res);
			dispatch('confirm', res);
		}
	};

	const saveRecording = (blob) => {
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		document.body.appendChild(a);
		a.style = 'display: none';
		a.href = url;
		a.download = 'recording.wav';
		a.click();
		window.URL.revokeObjectURL(url);
	};

	const startRecording = async () => {
		loading = true;

		stream = await navigator.mediaDevices.getUserMedia({
			audio: {
				echoCancellation: true,
				noiseSuppression: true,
				autoGainControl: true
			}
		});
		mediaRecorder = new MediaRecorder(stream);
		mediaRecorder.onstart = () => {
			console.log('Recording started');
			loading = false;
			startDurationCounter();

			audioChunks = [];
			// 检查 stream 是否仍然有效，避免在快速短按时出现错误
			if (stream) {
				analyseAudio(stream);
				if(!isPressingVoice && !recording){
					stopRecording();
				}
			}
		};
		mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);
		mediaRecorder.onstop = async () => {
			console.log('Recording stopped');
			if ($config.audio.stt.engine === 'web' || ($settings?.audio?.stt?.engine ?? '') === 'web') {
				audioChunks = [];
			} else {
				if (confirmed) {
					const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });

					await transcribeHandler(audioBlob);

					confirmed = false;
					loading = false;
				}
				audioChunks = [];
				recording = false;
			}
		};
		mediaRecorder.start();
		if ($config.audio.stt.engine === 'web' || ($settings?.audio?.stt?.engine ?? '') === 'web') {
			if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
				// Create a SpeechRecognition object
				speechRecognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();

				// Set continuous to true for continuous recognition
				speechRecognition.continuous = true;

				// Set the timeout for turning off the recognition after inactivity (in milliseconds)
				const inactivityTimeout = 2000; // 3 seconds

				let timeoutId;
				// Start recognition
				speechRecognition.start();

				// Event triggered when speech is recognized
				speechRecognition.onresult = async (event) => {
					// Clear the inactivity timeout
					clearTimeout(timeoutId);

					// Handle recognized speech
					console.log(event);
					const transcript = event.results[Object.keys(event.results).length - 1][0].transcript;

					transcription = `${transcription}${transcript}`;

					await tick();
					document.getElementById('chat-input')?.focus();

					// Restart the inactivity timeout
					timeoutId = setTimeout(() => {
						console.log('Speech recognition turned off due to inactivity.');
						speechRecognition.stop();
					}, inactivityTimeout);
				};

				// Event triggered when recognition is ended
				speechRecognition.onend = function () {
					// Restart recognition after it ends
					console.log('recognition ended');

					confirmRecording();
					dispatch('confirm', { text: transcription });
					confirmed = false;
					loading = false;
				};

				// Event triggered when an error occurs
				speechRecognition.onerror = function (event) {
					console.log(event);
					toast.error($i18n.t(`Speech recognition error: {{error}}`, { error: event.error }));
					dispatch('cancel');

					stopRecording();
				};
			}
		}
	};

	const stopRecording = async () => {
		if (mediaRecorder && mediaRecorder.state !== 'inactive') {
			await mediaRecorder.stop();
		}

		if (speechRecognition) {
			speechRecognition.stop();
		}

		stopDurationCounter();
		audioChunks = [];

		if (stream) {
			const tracks = stream.getTracks();
			tracks.forEach((track) => track.stop());
		}

		stream = null;
	};

	const confirmRecording = async () => {
		loading = true;
		confirmed = true;

		if (recording && mediaRecorder) {
			await mediaRecorder.stop();
		}
		clearInterval(durationCounter);

		if (stream) {
			const tracks = stream.getTracks();
			tracks.forEach((track) => track.stop());
		}

		stream = null;
	};

	let resizeObserver;
	let containerWidth;

	let maxVisibleItems = 300;
	$: maxVisibleItems = Math.floor(containerWidth / 5); // 2px width + 0.5px gap

	onMount(() => {
		// listen to width changes
		resizeObserver = new ResizeObserver(() => {
			VISUALIZER_BUFFER_LENGTH = Math.floor(window.innerWidth / 4);
			if (visualizerData.length > VISUALIZER_BUFFER_LENGTH) {
				visualizerData = visualizerData.slice(visualizerData.length - VISUALIZER_BUFFER_LENGTH);
			} else {
				visualizerData = Array(VISUALIZER_BUFFER_LENGTH - visualizerData.length)
					.fill(0)
					.concat(visualizerData);
			}
		});

		resizeObserver.observe(document.body);
	});

	onDestroy(() => {
		// remove resize observer
		resizeObserver.disconnect();
	});
</script>

<div
	bind:clientWidth={containerWidth}
	class="{showPressToTalk ? '' : loading
		? ' bg-gray-100/50 dark:bg-gray-850/50'
		: 'bg-primary-300/10 dark:bg-primary-500/10 '} rounded-full flex justify-between {className}"
>
	{#if !showPressToTalk}
		<div class="flex items-center mr-1">
			<button
				type="button"
				class="p-1.5

				{loading
					? ' bg-gray-200 dark:bg-gray-700/50'
					: 'bg-primary-400/20 text-primary-600 dark:text-primary-300 '}


				rounded-full"
				on:click={async () => {
					stopRecording();
					dispatch('cancel');
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="3"
					stroke="currentColor"
					class="size-4"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<div
			class="flex flex-1 self-center items-center justify-between ml-2 mx-1 overflow-hidden h-6"
			dir="rtl"
		>
			<div
				class="flex items-center gap-0.5 h-6 w-full max-w-full overflow-hidden overflow-x-hidden flex-wrap"
			>
				{#each visualizerData.slice().reverse() as rms}
					<div class="flex items-center h-full">
						<div
							class="w-[2px] shrink-0

						{loading
								? ' bg-gray-500 dark:bg-gray-400   '
								: 'bg-primary-500 dark:bg-primary-400  '}

						inline-block h-full"
							style="height: {Math.min(100, Math.max(14, rms * 100))}%;"
						/>
					</div>
				{/each}
			</div>
		</div>
	{/if}
	{#if showPressToTalk}
		<!-- 移动端按住说话按钮 -->
		<div class="w-full relative">
			<button
				type="button"
				class="w-full py-4 {isCancelGesture ? 'bg-red-500 hover:bg-red-600' : 'bg-primary-500 hover:bg-primary-600 active:bg-primary-700'} text-white rounded-2xl font-medium text-base transition-all duration-150 relative select-none"
				style="touch-action: none; -webkit-user-select: none;"
				on:pointerdown={async (e) => {
					e.preventDefault(); // 阻止默认行为
					isPressingVoice = true;
					isCancelGesture = false;
					pressStartY = e.clientY;
					currentY = e.clientY;
					pressStartTime = Date.now(); // 记录按下时间
				}}
				on:pointermove={(e) => {
					if (isPressingVoice) {
						e.preventDefault(); // 阻止默认行为
						currentY = e.clientY;
						const deltaY = pressStartY - currentY;
						
						// 上滑超过阈值时，只改变视觉状态（按钮变红、文字变化）
						// 不会立即取消录音，只是标记为取消手势
						// 如果用户滑回来（小于阈值），可以恢复正常状态
						if (deltaY > CANCEL_THRESHOLD) {
							isCancelGesture = true;
						} else {
							isCancelGesture = false;
						}
					}
				}}
				on:pointerup={async () => {
					console.log("pointerup");
					if (!isPressingVoice) return;
					
					const pressDuration = Date.now() - pressStartTime; // 计算按压时长
					isPressingVoice = false;
					
					// 检查按压时长是否满足最小要求
					if (pressDuration < MIN_PRESS_DURATION) {
						toast.warning("说话时间太短");
						// 按压时长不足，取消录音
						if (recording) {
							recording = false;
						}
						isCancelGesture = false;
						return;
					}
					
					// 只有在松手时才真正执行取消或发送操作
					// 如果此时处于取消手势状态（上滑超过阈值），则取消录音
					// 如果此时处于正常状态（未上滑或已滑回），则发送消息
					if (isCancelGesture) {
						// 上滑状态下松手：取消录音
						if (recording) {
							recording = false;
						}
						isCancelGesture = false;
					} else {
						// 正常状态下松手：发送消息
						if (recording) {
							// VoiceRecording组件会处理录音结束并触发confirm事件
							// 在confirm事件中会自动发送
							recording = false;
							confirmed = true;
						}
					}
				}}
				on:pointercancel={async () => {
					if (!isPressingVoice) return;
					
					const pressDuration = Date.now() - pressStartTime; // 计算按压时长
					isPressingVoice = false;
					
					// 检查按压时长是否满足最小要求
					if (pressDuration < MIN_PRESS_DURATION) {
						toast.warning("说话时间太短");
						// 按压时长不足，取消录音
						if (recording) {
							recording = false;
						}
						isCancelGesture = false;
						return;
					}
					
					// 将 pointercancel 视为类似 pointerup 的情况
					// 根据当前的手势状态来决定是取消还是继续录音
					
					if (isCancelGesture) {
						// 如果处于取消手势状态，则取消录音
						if (recording) {
							recording = false;
						}
						isCancelGesture = false;
					} else {
						// 如果不在取消手势状态，则正常发送
						if (recording) {
							recording = false;
						}
					}
				}}
			>
				<div class="flex flex-col items-center">
					<span class="text-base">{isCancelGesture ? '松开取消' : '按住说话'}</span>
					{#if isPressingVoice && !isCancelGesture}
						<span class="text-xs mt-1 opacity-80">↑ 上滑取消</span>
					{/if}
				</div>
			</button>
		</div>
	{/if}
	{#if !showPressToTalk}
		<div class="flex">
			<div class="  mx-1.5 pr-1 flex justify-center items-center">
				<div
					class="text-sm


			{loading ? ' text-gray-500  dark:text-gray-400  ' : ' text-primary-400 '}
		font-medium flex-1 mx-auto text-center"
				>
					{formatSeconds(durationSeconds)}
				</div>
			</div>

			<div class="flex items-center">
				{#if loading}
					<div class=" text-gray-500 rounded-full cursor-not-allowed">
						<svg
							width="24"
							height="24"
							viewBox="0 0 24 24"
							xmlns="http://www.w3.org/2000/svg"
							fill="currentColor"
							><style>
								.spinner_OSmW {
									transform-origin: center;
									animation: spinner_T6mA 0.75s step-end infinite;
								}
								@keyframes spinner_T6mA {
									8.3% {
										transform: rotate(30deg);
									}
									16.6% {
										transform: rotate(60deg);
									}
									25% {
										transform: rotate(90deg);
									}
									33.3% {
										transform: rotate(120deg);
									}
									41.6% {
										transform: rotate(150deg);
									}
									50% {
										transform: rotate(180deg);
									}
									58.3% {
										transform: rotate(210deg);
									}
									66.6% {
										transform: rotate(240deg);
									}
									75% {
										transform: rotate(270deg);
									}
									83.3% {
										transform: rotate(300deg);
									}
									91.6% {
										transform: rotate(330deg);
									}
									100% {
										transform: rotate(360deg);
									}
								}
							</style><g class="spinner_OSmW"
								><rect x="11" y="1" width="2" height="5" opacity=".14" /><rect
									x="11"
									y="1"
									width="2"
									height="5"
									transform="rotate(30 12 12)"
									opacity=".29"
								/><rect
									x="11"
									y="1"
									width="2"
									height="5"
									transform="rotate(60 12 12)"
									opacity=".43"
								/><rect
									x="11"
									y="1"
									width="2"
									height="5"
									transform="rotate(90 12 12)"
									opacity=".57"
								/><rect
									x="11"
									y="1"
									width="2"
									height="5"
									transform="rotate(120 12 12)"
									opacity=".71"
								/><rect
									x="11"
									y="1"
									width="2"
									height="5"
									transform="rotate(150 12 12)"
									opacity=".86"
								/><rect x="11" y="1" width="2" height="5" transform="rotate(180 12 12)" /></g
							></svg
						>
					</div>
				{:else}
					<button
						type="button"
						class="p-1.5 bg-primary-500 text-white dark:bg-primary-500 dark:text-primary-950 rounded-full"
						on:click={async () => {
							await confirmRecording();
						}}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="2.5"
							stroke="currentColor"
							class="size-4"
						>
							<path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
						</svg>
					</button>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.visualizer {
		display: flex;
		height: 100%;
	}

	.visualizer-bar {
		width: 2px;
		background-color: #4a5aba; /* or whatever color you need */
	}
</style>
