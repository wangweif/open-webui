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
        
        await goto('/', { replaceState: true });
        // 点击"新对话"按钮，触发与点击"新对话"按钮相同的逻辑
        const newChatButton = document.getElementById('new-chat-button');
        setTimeout(() => {
            newChatButton?.click();
            // 如果是移动端，关闭侧边栏提高用户体验
            if ($mobile) {
                showSidebar.set(false);
            }
            
            // 如果临时聊天开启，更新URL参数
            if ($temporaryChatEnabled) {
                history.replaceState(null, '', `?temporary-chat=true`);
            }
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
        // 否则根据模型类型使用默认图标
        else if (model.owned_by === 'openai') { 
            return `
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" class="w-5 h-5">
                <path d="M10.08 7.0133C10.0772 6.2617 9.78703 5.54064 9.28036 4.98904C8.77369 4.43744 8.08516 4.09333 7.33986 4.02253C6.59456 3.95174 5.85111 4.15916 5.24316 4.60277C4.63521 5.04638 4.20501 5.69642 4.03626 6.42797C3.63201 6.57328 3.2698 6.81097 2.98139 7.12115C2.69298 7.43133 2.48687 7.80392 2.38117 8.20798C2.27548 8.61203 2.27366 9.03584 2.37588 9.44073C2.47809 9.84562 2.68103 10.22 2.96696 10.5326C2.8418 10.8117 2.7724 11.1131 2.76272 11.4191C2.75304 11.7251 2.80328 12.0299 2.91039 12.3161C3.0175 12.6022 3.17903 12.8645 3.38604 13.0887C3.59306 13.3129 3.84169 13.4948 4.11886 13.6242C4.39604 13.7537 4.69623 13.8283 5.00134 13.844C5.30646 13.8597 5.61269 13.8161 5.9019 13.7154C6.19111 13.6146 6.4573 13.4587 6.68435 13.2566C6.91141 13.0546 7.09498 12.8102 7.22494 12.5363C7.95672 12.6266 8.69983 12.4498 9.3183 12.0404C9.93678 11.631 10.3848 11.0182 10.5733 10.3126C11.0462 10.1236 11.4543 9.80397 11.7473 9.39281C12.0404 8.98166 12.2058 8.49704 12.2236 7.99818C12.2413 7.49932 12.1106 7.00533 11.8472 6.57522C11.5837 6.14511 11.1991 5.79961 10.7413 5.58063V5.57997C10.558 5.98345 10.27 6.34078 9.90088 6.61554C9.53178 6.89031 9.09731 7.0733 8.63586 7.1453C8.4724 6.77048 8.21071 6.44232 7.87834 6.18938C7.54596 5.93644 7.15499 5.76741 6.74347 5.69869C6.33196 5.62997 5.9126 5.66401 5.51799 5.79778C5.12339 5.93156 4.76622 6.1615 4.48119 6.46863C4.28473 6.26625 4.14323 6.01584 4.07213 5.74368C4.00102 5.47152 4.00252 5.18587 4.07651 4.91456C4.1505 4.64325 4.29465 4.3947 4.49321 4.19496C4.69177 3.99522 4.93985 3.85045 5.21147 3.77585C5.4831 3.70126 5.769 3.69945 6.04171 3.77062C6.31442 3.84179 6.56442 3.98341 6.76557 4.18054C6.96673 4.37768 7.11408 4.62426 7.19161 4.8945C7.26914 5.16474 7.27438 5.4503 7.20678 5.72284C7.87221 5.95374 8.45191 6.37714 8.8628 6.93411C9.27369 7.49108 9.49633 8.1538 9.4986 8.83198V8.83198C9.4986 9.07198 9.47327 9.31065 9.42327 9.54398C9.14254 9.74108 8.81987 9.87566 8.4792 9.93801C8.13853 10.0004 7.79037 9.98922 7.45719 9.90537C7.37886 10.2093 7.24087 10.3973 7.05253 10.5532C6.86419 10.7092 6.63068 10.8292 6.37453 10.9053C6.11839 10.9813 5.84667 11.0118 5.57788 10.9949C5.30909 10.978 5.0478 10.914 4.8092 10.8066C4.7119 10.9713 4.64599 11.1536 4.61558 11.3427C4.58518 11.5319 4.5909 11.7251 4.6324 11.9121C4.67389 12.0991 4.75038 12.2763 4.85743 12.4342C4.96447 12.5921 5.09993 12.7275 5.25493 12.834C5.40994 12.9404 5.58175 13.016 5.7626 13.0568C5.94345 13.0977 6.13037 13.1029 6.31325 13.0722C6.49613 13.0416 6.671 12.9757 6.8299 12.8786C6.9888 12.7814 7.12692 12.6545 7.2358 12.5053C7.34867 12.3515 7.42712 12.1777 7.46613 11.994C7.50515 11.8103 7.5039 11.6207 7.46248 11.4375C7.61673 11.35 7.75694 11.2417 7.88 11.1148C8.00113 10.9894 8.1014 10.8413 8.17333 10.68L8.17267 10.678C8.54095 10.7699 8.92394 10.7874 9.29931 10.7294C9.67469 10.6714 10.0346 10.5389 10.3566 10.3393C10.4186 10.5971 10.5347 10.8384 10.6977 11.0476C10.8607 11.2567 11.0671 11.4284 11.304 11.5515C11.5409 11.6747 11.8029 11.7461 12.0724 11.7615C12.3419 11.7768 12.6119 11.7357 12.8619 11.6413C13.112 11.5469 13.3358 11.4015 13.518 11.2153C13.7003 11.0291 13.837 10.8071 13.9183 10.564C13.9997 10.3208 14.0235 10.0629 13.9879 9.80898C13.9523 9.55501 13.8583 9.31174 13.7136 9.09838C13.5688 8.88502 13.3773 8.708 13.154 8.5812C12.9307 8.4544 12.6818 8.37999 12.426 8.3642C12.1702 8.3484 11.9144 8.3916 11.678 8.49064V8.49064C11.5366 8.02732 11.2311 7.62599 10.8166 7.35821C10.4022 7.09043 9.90574 6.9726 9.41194 7.02797L10.08 7.0133Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>`;
        } else if (model.owned_by === 'ollama') {
            return `
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" class="w-5 h-5">
                <path d="M3.33331 12L8.00001 14.6667L12.6667 12M3.33331 8L8.00001 10.6667L12.6667 8M8.00001 1.33334L3.33331 4.00001L8.00001 6.66668L12.6667 4.00001L8.00001 1.33334Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>`;
        } else {
            return `
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" class="w-5 h-5">
                <path d="M6.00001 13.3333H10M4.66668 3.33334H11.3333C12.0667 3.33334 12.6667 3.93334 12.6667 4.66668V9.33334C12.6667 10.0667 12.0667 10.6667 11.3333 10.6667H4.66668C3.93334 10.6667 3.33334 10.0667 3.33334 9.33334V4.66668C3.33334 3.93334 3.93334 3.33334 4.66668 3.33334Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>`;
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