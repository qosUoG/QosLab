<script lang="ts" generics="T extends Experiment | Equipment">
	import { autofocus } from "$components/utils.svelte";
	import Cancel from "$icons/Cancel.svelte";
	import Edit from "$icons/Edit.svelte";
	import Reload from "$icons/Reload.svelte";
	import Tick from "$icons/Tick.svelte";
	import type { Experiment, Equipment } from "qoslab-shared";
	import Separator from "./Separator.svelte";
	import Select from "$components/reuseables/Select.svelte";

	let {
		module = $bindable(),
		cls = $bindable(),
		options,
		onconfirm,
	}: {
		module: string | undefined;
		cls: string | undefined;
		options: string[];
		onconfirm: (path: { module: string; cls: string }) => void;
	} = $props();

	let target_path_defined = $derived(
		module !== undefined && cls !== undefined && module !== "" && cls !== ""
	);
	let editing = $state(module === undefined || cls === undefined);
	let temp_path = $state(
		(() => (target_path_defined ? `${module} ${cls}` : ""))()
	);
</script>

<div class="row-2 min-w-0">
	{#if editing}
		<div class="row-2 bg-white wrapped flex-grow min-w-0 h-full">
			<div class="editor-label">Path</div>
			<Separator />
			<div
				class="relative flex-grow -mx-2 px-2 flex items-center min-w-0">
				<Select bind:value={temp_path} {options} />
			</div>
		</div>
		<div class="row-1">
			{#if editing && target_path_defined}
				<button
					class="icon-btn-sm red"
					onclick={() => {
						temp_path = `${module} ${cls}`;
						editing = false;
					}}><Cancel /></button>
			{:else}
				<div class="icon-btn-sm"></div>
			{/if}
			<button
				class="icon-btn-sm green"
				onclick={() => {
					if (temp_path === "") return;

					editing = false;

					if (temp_path === `${module} ${cls}`) return;

					const [rmodule, rcls] = temp_path.split(" ");

					module = rmodule;
					cls = rcls;
					onconfirm({ module: rmodule, cls: rcls });
				}}><Tick /></button>
		</div>
	{:else}
		<div class="row-2 bg-white wrapped min-w-0 flex-grow">
			<div class="editor-label">Path</div>
			<div class="w-0.5 bg-slate-200 rounded-full"></div>
			<div class="min-w-0">
				<div class="overflow-x-scroll text-nowrap">{temp_path}</div>
			</div>
		</div>
		<div class="row-1">
			<button
				class="icon-btn-sm slate"
				onclick={() => {
					onconfirm({ module: module!, cls: cls! });
				}}><Reload /></button>
			<button
				class="icon-btn-sm slate"
				onclick={() => {
					editing = true;
				}}><Edit /></button>
		</div>
	{/if}
</div>
