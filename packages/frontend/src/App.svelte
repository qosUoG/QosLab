<script lang="ts">
	import Mode from "$components/modules/Mode.svelte";
	import ProjectPath from "$components/modules/ProjectPath.svelte";

	import { gstore, type Log } from "$states/global.svelte";

	import Config from "$components/modules/config/Config.svelte";
	import Experiments from "$components/modules/runtime/Runtime.svelte";
	import Cli from "$icons/Cli.svelte";
	import CliPanel from "$components/modules/CliPanel.svelte";
	import { backendWs } from "$services/utils";

	import Toast from "$components/modules/Toast.svelte";

	let show_cli = $state(false);

	function connectWs() {
		// Connect to backend
		let ws = new WebSocket(backendWs("cli"));
		ws.onmessage = async (event: MessageEvent<string>) => {
			const payload = JSON.parse(event.data) as { logs: Log[] };
			gstore.logs.push(payload.logs);
		};
		ws.onclose = () => {
			// Recursively reconnect
			connectWs();
		};
	}

	connectWs();
</script>

<div class="fcol-4 w-full h-full p-4 relative">
	<div class="frow-4 w-full items-stretch">
		<Mode />
		<ProjectPath />
		<button
			class="icon-btn-sm bg-slate-500 text-white"
			onclick={() => {
				show_cli = !show_cli;
			}}><Cli /></button>
	</div>

	<div class="h-full w-full frow-4 min-h-0 relative">
		{#if !gstore.workspace.connected}
			<div
				class="h-full w-full z-100 absolute top-0 left-0 backdrop-blur-xs rounded flex justify-center items-center">
				<div class="text-3xl bg-white p-20 rounded">
					Connect to a workspace to begin
				</div>
			</div>
		{/if}
		{#if gstore.mode === "Configuration"}
			<Config />
		{:else if gstore.mode === "Runtime"}
			<Experiments />
		{/if}
		{#if show_cli}
			<CliPanel />
		{/if}
	</div>
	<Toast />
</div>
