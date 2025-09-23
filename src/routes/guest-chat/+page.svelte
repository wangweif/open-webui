<script lang="ts">
	import { json } from "@sveltejs/kit";
	import { onMount } from "svelte";
	import ContentRenderer from '$lib/components/chat/Messages/ContentRenderer.svelte';

	let messages = [];
	let inputValue = '';
	let isLoading = false;
	let messagesContainer;

	// Scroll to bottom when new messages are added
	$: if (messagesContainer) {
		messagesContainer.scrollTop = messagesContainer.scrollHeight;
	}
	let assistant_id = '5207a2b0349111f0a58a09681006223d';
	let session_id = '';	

	async function sendMessage() {
		// 获取session_id
		const question = inputValue;
		inputValue = '';
		if(!session_id || session_id == ''){
			const chat_id = crypto.randomUUID();
			const sessionReponse = await fetch(`https://know.baafs.net.cn/api/v1/chats/${assistant_id}/sessions`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': 'Bearer ragflow-cwZWU5YjBjMzUxODExZjBhNThhMDk2OD' 
				},
				body : JSON.stringify({name: chat_id})
			});
			console.log(sessionReponse)
			const res = await sessionReponse.json();
			session_id = res.data.id;
			console.log(session_id);
		}
		if (!question.trim() || isLoading) return;

		const userMessage = {
			id: Date.now(),
			role: 'user',
			content: question
		};
		messages = [...messages, userMessage];
		isLoading = true;

		const assistantMessage = {
			id: Date.now() + 1,
			role: 'assistant',
			content: ''
		};
		messages = [...messages, assistantMessage];

		try {
			// Get assistant_id from URL parameter or use default
			
			const response = await fetch(`https://know.baafs.net.cn/api/v1/chats/${assistant_id}/completions`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': 'Bearer ragflow-cwZWU5YjBjMzUxODExZjBhNThhMDk2OD' 
				},
				body: JSON.stringify({
					question: question,
					session_id: session_id,
					stream: true
				})
			});

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}
			inputValue = '';

			// Handle streaming response
			const reader = response.body?.getReader();
			const decoder = new TextDecoder();
			let accumulatedContent = '';

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				const chunk = decoder.decode(value);
				const lines = chunk.split('\n');

				for (const line of lines) {
					let json_data = null
					if(line){
						json_data = JSON.parse(line.slice(5));
					}
					if (json_data?.data) {
						const data = json_data.data;
						console.log(data);
						if (data === true) continue;
						
						try {
							accumulatedContent = data.answer;
							// 移除<think> 和 </think>标签
							accumulatedContent = accumulatedContent.replace(/<think>[\s\S]*?<\/think>/g, '');
							// Update the last message (assistant message)
							messages = messages.map((msg, index) => 
								index === messages.length - 1 
									? { ...msg, content: accumulatedContent }
									: msg
							);

							// 提取参考链接
							if(data.reference?.chunks){
								
								if(data.reference.chunks.length > 0){
									accumulatedContent += `\n\n**链接**`
									for(const chunk of data.reference.chunks){
										const filename = chunk.document_name;
										const parts = filename.split(".");
										// 移除文件后缀
										parts.pop();
										// 转为string
										let processed_filename = parts.join(".");
										// 提取并移除[]中的内容
										let url = processed_filename.match(/\[(.*?)\]/)?.[1];
										if(url){
											processed_filename = processed_filename.replace(`[${url}]`, '');
										}
										// url解码
										url = decodeURIComponent(url);
										// 拼接 preview_url
										const reference = `\n\n - [${processed_filename}](${url})`;
										accumulatedContent += reference;
									}
									messages = messages.map((msg, index) => 
										index === messages.length - 1 
											? { ...msg, content: accumulatedContent }
											: msg
									);
								}
								
							}
						} catch (e) {
							console.error('Error parsing SSE data:', e);
						}
					}
				}
			}
		} catch (error) {
			console.error('Error sending message:', error);
			messages = messages.map((msg, index) => 
				index === messages.length - 1 
					? { ...msg, content: '抱歉，发生了错误。请稍后重试。' }
					: msg
			);
		} finally {
			isLoading = false;
		}
	}

	function handleKeydown(event) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage();
		}
	}
</script>

<svelte:head>
	<title>游客对话</title>
</svelte:head>

<div class="flex flex-col h-screen bg-gray-50">
	<!-- Hidden header to prevent menu display -->
	<div class="hidden"></div>
	
	<!-- Messages Container -->
	<div 
		bind:this={messagesContainer}
		class="flex-1 overflow-y-auto px-4 py-6"
	>
		<div class="max-w-4xl mx-auto">
			{#if messages.length === 0}
				<div class="text-center text-gray-500 mt-20">
					<div class="text-4xl mb-4">💬</div>
					<h2 class="text-xl font-semibold mb-2">欢迎使用游客对话</h2>
					<p>请在下方输入您的问题，我会尽力为您解答。</p>
				</div>
			{/if}
			
			{#each messages as message}
				<div class="mb-6 flex {message.role === 'user' ? 'justify-end' : 'justify-start'}">
					<div 
						class="max-w-3xl px-4 py-3 rounded-lg {message.role === 'user' 
							? 'bg-blue-500 text-white' 
							: 'bg-white text-gray-800 border border-gray-200'
						}"
					>
						{#if message.role === 'user'}
							{message.content}
						{:else}
							<ContentRenderer
								id={message.id}
								history={messages}
								content={message.content}
								floatingButtons={false}
								save={false}
							/>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	</div>
	
	<!-- Input Area -->
	<div class="border-t border-gray-200 bg-white px-4 py-4">
		<div class="max-w-4xl mx-auto">
			<div class="flex items-end space-x-4">
				<textarea
					bind:value={inputValue}
					on:keydown={handleKeydown}
					placeholder="输入您的问题..."
					class="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					rows="1"
					disabled={isLoading}
				></textarea>
				<button
					on:click={sendMessage}
					disabled={!inputValue.trim() || isLoading}
					class="px-6 py-3 bg-blue-500 text-white rounded-lg whitespace-nowrap hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
				>
					发送
				</button>
			</div>
		</div>
	</div>
</div>

<style>
	/* Hide any menu or navigation elements */
	:global(.sidebar, .navigation, .menu, .header-menu) {
		display: none !important;
	}
	
	/* Ensure page takes full viewport */
	:global(body) {
		overflow: hidden;
	}
</style>