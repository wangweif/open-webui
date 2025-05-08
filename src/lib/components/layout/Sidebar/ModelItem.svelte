<script lang="ts">
    import { goto } from '$app/navigation';
    import { settings, mobile, showSidebar, type Model, chatId, temporaryChatEnabled } from '$lib/stores';
    import { getContext, onMount } from 'svelte';
    import { createNewChat } from '$lib/apis/chats';
    import { toast } from 'svelte-sonner';
    import { updateUserSettings } from '$lib/apis/users';
    const i18n = getContext('i18n');

    export let model: Model;
    
    // 在组件加载时检查localStorage中是否有保存的默认模型
    onMount(() => {
        // 如果localStorage中有保存的模型设置，则更新store
        const savedSettings = localStorage.getItem('modelSettings');
        if (savedSettings) {
            try {
                const parsedSettings = JSON.parse(savedSettings);
                if (parsedSettings.models) {
                    settings.update(s => {
                        return { ...s, models: parsedSettings.models };
                    });
                }
            } catch (e) {
                console.error('Error parsing saved model settings:', e);
            }
        }
    });

    // 点击模型后设置默认模型并导航到聊天界面
    async function selectModel() {
        // 首先保存到localStorage确保持久化
        localStorage.setItem('modelSettings', JSON.stringify({ models: [model.id] }));
        // 然后更新settings store
        settings.update(s => {
            return { ...s, models: [model.id] };
        });
        await updateUserSettings(localStorage.token, { ui: $settings });
        
        // 点击"新对话"按钮，触发与点击"新对话"按钮相同的逻辑
        const newChatButton = document.getElementById('sidebar-new-chat-button');
        setTimeout(() => {
            newChatButton?.click();
        }, 0);
    }

    // 获取模型描述，兼容不同类型的模型
    function getDescription(model: Model): string | undefined {
        if ('description' in model) {
            return model.description;
        } else if (model.info?.meta?.description) {
            return model.info.meta.description;
        }
        return undefined;
    }

    // 根据模型类型返回不同的图标
    function getModelIcon(model: Model) {
        // 如果模型有自己的图标（通过meta.profile_image_url），优先使用
        if (model.info?.meta?.profile_image_url) {
            return `<img src="${model.info.meta.profile_image_url}" class="w-5 h-5 rounded-full object-cover" alt="${model.name}" />`;
        }
        // 否则使用默认图标
        else{
            return `<img src="/static/favicon.png" class="w-5 h-5 rounded-full object-cover" alt="${model.name}" />`;
        }
    }

    // 使用响应式声明，确保模型图标在界面刷新后能正确加载
    $: modelIcon = getModelIcon(model);
    $: description = getDescription(model);

    // 可视化当前是否选中（是否为默认模型）
    $: {
        // 如果store中没有models设置，先检查localStorage
        if (!$settings?.models || $settings.models.length === 0) {
            try {   
                const savedSettings = localStorage.getItem('modelSettings');
                if (savedSettings) {
                    const parsedSettings = JSON.parse(savedSettings);
                    if (parsedSettings.models && parsedSettings.models.length > 0) {
                        settings.update(s => {
                            return { ...s, models: parsedSettings.models };
                        });
                    }
                }
            } catch (e) {
                console.error('Error checking saved model settings:', e);
            }
        }
    }
    
    // 检查模型是否被选中
    $: isSelected = $settings?.models?.includes(model.id) || false;
</script>

<button 
    class="w-full flex items-center rounded-lg px-2 py-1.5 hover:bg-gray-100 dark:hover:bg-gray-900 transition {isSelected ? 'bg-gray-100 dark:bg-gray-800' : ''}"
    on:click={selectModel}
>
    <div class="flex flex-row items-center w-full">
        <div class="mr-2.5 flex-shrink-0 text-gray-600 dark:text-gray-400 w-6 h-6 flex items-center justify-center">
            {@html modelIcon}
        </div>
        <div class="flex-1 overflow-hidden">
            <div class="font-medium text-sm text-left truncate text-gray-800 dark:text-gray-200">
                {model.name}
            </div>
            {#if description}
            <div class="text-xs text-left truncate text-gray-600 dark:text-gray-400">
                {description}
            </div>
            {/if}
        </div>
        {#if isSelected}
        <div class="flex-shrink-0 text-blue-500">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="size-4">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
        </div>
        {/if}
    </div>
</button> 