<script lang="ts">
    import { onMount } from 'svelte';    
    import { showSidebar } from '$lib/stores';    
    import MenuLines from '$lib/components/icons/MenuLines.svelte';
    
    let iframeElement: HTMLIFrameElement;
    let iframeSrc: string = '';
    let title: string = '外部应用';
    
    onMount(() => {
        // 从URL参数中获取iframe src和标题
        const urlParams = new URLSearchParams(window.location.search);
        iframeSrc = urlParams.get('src') || '';
        title = urlParams.get('title') || '外部应用';
        
        if (!iframeSrc) {
            console.error('无效的iframe URL');
        }
    });
   
</script>

<div class="w-full h-full flex flex-col">
    <div class="flex items-center justify-between p-1">
        <div class="flex items-center">
            <button
                id="sidebar-toggle-button"
                class="{$showSidebar ? 'md:hidden' : ''} cursor-pointer p-1.5 flex rounded-xl hover:bg-gray-100 dark:hover:bg-gray-850 transition mr-2"
                on:click={() => {
                    showSidebar.set(!$showSidebar);
                }}
                aria-label="Toggle Sidebar"
            >
                <div class="m-auto self-center">
                    <MenuLines />
                </div>
            </button>
            <!-- <h1 class="text-lg font-medium text-gray-900 dark:text-white">{title}</h1> -->
        </div>
    </div>
    
    <div class="flex-1 w-full">
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
                <p class="text-gray-500 dark:text-gray-400">{'未提供有效的iframe URL'}</p>
            </div>
        {/if}
    </div>
</div> 