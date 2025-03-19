import type { ChartConfigs, Experiment } from "qoslab-shared"

export type RuntimeExperiment = Experiment & {
    charts: Record<string, ChartConfigs>

    status: "initial" | "starting" | "started" | "pausing" | "paused" | "continuing" | "continued" | "stopping" | "stopped" | "completed"

    loop_count: number
    proposed_total_loop?: number

    total_time: number
    loop_time_start: number
    timer?: Timer



    ws?: WebSocket

}

export type CreatedRuntimeExperiment = Extract<RuntimeExperiment, { created: true }>

export function getExperimentEventFn(experiment: CreatedRuntimeExperiment) {

    function updateEventFromWsFn(event: MessageEvent<string>) {

        console.log(event.data)

        const res = JSON.parse(event.data) as
            { key: "loop_count", value: number } |
            { key: "proposed_total_loop", value: number }
            | { key: "status", value: "started" | "paused" | "continued" | "completed" | "initial" | "stopped" }

        // Pleasing the type checker
        if (typeof res.value === "number")
            experiment[res.key] = res.value
        else
            experiment[res.key] = res.value

        if (res.key === "status") {
            switch (res.value) {
                case "started":
                    experiment.total_time = 0
                    experiment.loop_time_start = 0
                    experiment.loop_count = 0
                    experiment.timer = setInterval(() => {
                        experiment.total_time += 1
                    }, 1000)
                    break
                case "continued":
                    // reset loop time
                    experiment.loop_time_start = experiment.total_time
                    experiment.timer = setInterval(() => {
                        experiment.total_time += 1
                    }, 1000)
                    break
                case "paused":
                case "completed":
                case "stopped":
                    clearInterval(experiment.timer)
                    break
            }
        }

        // Reset loop time
        if (res.key === "loop_count")

            experiment.loop_time_start = experiment.total_time


    }

    return updateEventFromWsFn
}