<script lang="ts">
	import DependencyEditor from "./Dependency/DependencyEditor.svelte";
	import { editor } from "./EditorController.svelte";
	import EeEditor from "./ee/EEEditor.svelte";
</script>

{#if editor.mode === "dependency"}
	<DependencyEditor />
{:else if editor.mode === "ee"}
	<EeEditor />
{:else if editor.mode !== undefined}
	editor.mode unexpected value!!!
{:else}
	<div class="section bg-slate-200 col-span-2"></div>
{/if}
