<script lang="ts">
	import Mode from "$components/modules/Mode.svelte";
	import ProjectPath from "$components/modules/ProjectPath.svelte";

	import { gstore } from "$states/global.svelte";

	import Config from "$components/modules/config/Config.svelte";
	import Experiments from "$components/modules/experiments/Experiments.svelte";
	import Cli from "$icons/Cli.svelte";
	import CliPanel from "$components/modules/CliPanel.svelte";

	let show_cli = $state(false);
</script>

<div class="col-4 w-full h-full p-4">
	<div class="row-4 w-full items-stretch">
		<Mode />
		<ProjectPath />
		<button
			class="icon-btn-sm bg-slate-500 text-white"
			onclick={() => {
				show_cli = !show_cli;
			}}><Cli /></button>
	</div>

	<div class="h-full w-full row-4 min-h-0">
		{#if gstore.mode === "CONFIG"}
			<Config />
		{:else if gstore.mode === "EXPERIMENTS"}
			<Experiments />
		{/if}
		{#if show_cli}
			<CliPanel />
		{/if}
	</div>
</div>
