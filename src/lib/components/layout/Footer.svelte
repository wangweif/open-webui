<script>
    export let is_bjny = false
</script>

<div class="w-full px-4 text-center text-xs text-gray-500 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 mt-auto whitespace-pre-wrap">
    {#if is_bjny}
        {FOOTER_TEXT_BJNY || "内容由 AI大模型生成，请仔细甄别。技术支持:北京市农林科学院"}
    {:else}
        {FOOTER_TEXT || "内容由 AI大模型生成，请仔细甄别。技术支持:北京市农林科学院"}
    {/if}
</div>
<div class="w-full px-4 text-center text-xs dark:border-gray-700 bg-white dark:bg-gray-900 mt-auto whitespace-pre-wrap text-red-500 dark:text-red-400">
    {"禁止在系统内传输、存储、处理涉密文件和信息"}  
</div>