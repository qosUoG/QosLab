<script lang="ts">
	import { getRandomId } from "$lib/utils";

	import {
		readAllUvDependencies,
		setWorkspaceDirectory,
	} from "$services/backend.svelte";
	import { getAvailableEEs } from "$services/qoslabapp.svelte";

	import { gstore } from "$states/global.svelte";
	import { retryOnError, type Dependency } from "qoslab-shared";
</script>

<label class=" row-1 flex-grow">
	<div class="w-fit wrapped text-nowrap bg-slate-200 flex items-center">
		Project Directory
	</div>
	<input
		spellcheck="false"
		class="flex-grow wrapped bg-slate-200"
		type="text"
		bind:value={gstore.workspace.path} />
	<button
		class="wrapped slate"
		onclick={async () => {
			// set the project directory
			await setWorkspaceDirectory(gstore.workspace.path);

			// fetch the dependency from pyproject.toml
			const new_dependencies: Record<string, Dependency> = {};

			(await readAllUvDependencies()).forEach((d) => {
				const id = getRandomId(Object.keys(new_dependencies));

				new_dependencies[id] = { ...d, id };
			});

			gstore.workspace.dependencies = new_dependencies;

			gstore.workspace.available_equipments =
				await getAvailableEEs("equipment");

			gstore.workspace.available_experiments =
				await getAvailableEEs("experiment");
		}}>Set</button>
</label>
