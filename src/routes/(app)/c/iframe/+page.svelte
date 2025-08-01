<script lang="ts">
    import { onMount, getContext } from 'svelte';
    import { showSidebar, user } from '$lib/stores';
    import { page } from '$app/stores';
    import Navbar from '$lib/components/chat/Navbar.svelte';

    // 全局环境变量
    declare global {
        const BUILD_TARGET: string;
        const FOOTER_TEXT: string;
        const FOOTER_TEXT_BJNY: string;
    }

    const i18n = getContext('i18n');

    let iframeElement: HTMLIFrameElement;
    let iframeSrc: string = '';
    let title: string = '外部应用';

    // 简化的聊天数据，用于Navbar组件
    let selectedModels: any[] = [];
    let history = { currentId: null };

    // 监听URL参数变化并更新iframe内容
    $: {
        if ($page.url.searchParams) {
            const newSrc = $page.url.searchParams.get('src') || '';
            const newTitle = $page.url.searchParams.get('title') || '外部应用';
            
            if (newSrc !== iframeSrc || newTitle !== title) {
                iframeSrc = newSrc;
                title = newTitle;
                
                if (!iframeSrc) {
                    console.error('无效的iframe URL');
                }
            }
        }
    }

    // 空函数，用于满足Navbar组件要求
    const initNewChat = () => {};

</script>

<!-- 使用完整的聊天界面布局 -->
<div
    class="h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
        ? 'md:max-w-[calc(100%-260px)]'
        : ''} w-full max-w-full flex flex-col"
    id="chat-container"
>
    <!-- 顶部导航栏，包含用户头像 -->
    <Navbar
        chat={{
            id: null,
            chat: {
                title: title,
                models: selectedModels,
                system: undefined,
                params: {},
                history: history,
                timestamp: Date.now()
            }
        }}
        {history}
        title={title}
        bind:selectedModels
        shareEnabled={false}
        {initNewChat}
        showModelSelector={false}
    />

    <!-- 主要内容区域 -->
    <div class="flex flex-col flex-auto z-10 w-full @container">
        <div class="flex-1 max-h-full overflow-hidden">
            {#if iframeSrc}
                <iframe
                    bind:this={iframeElement}
                    src={iframeSrc}
                    title={title}
                    class="w-full h-full border-0"
                    sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-downloads"
                ></iframe>
            {:else}
                <div class="w-full h-full flex items-center justify-center">
                    <p class="text-gray-500 dark:text-gray-400">未提供有效的iframe URL</p>
                </div>
            {/if}
        </div>

        <!-- 底部技术支持信息 -->
        <div class="w-full py-2 px-4 text-center text-xs text-gray-500 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
            {#if $user?.is_bjny}
                {FOOTER_TEXT_BJNY || "内容由 AI大模型生成，请仔细甄别。技术支持:北京市农林科学院"}
            {:else}
                {FOOTER_TEXT || "内容由 AI大模型生成，请仔细甄别。技术支持:北京市农林科学院"}
            {/if}
        </div>
    </div>
</div>