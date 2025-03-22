import type { AllParamTypes } from "./params"

export type EEType = "equipment" | "experiment"

export type ModuleCls = {
    module: string,
    cls: string
}

type Params = Record<string, AllParamTypes>

type EENotCreated = {
    created: false
    id: string
    // created in the python qoslabapp?
    // If created, the module and cls would be defined
    // the params would be collected as well
    module_cls: ModuleCls
}

type EECreated = {
    created: true
    id: string

    module_cls: ModuleCls

    name: string

    params: Params
    temp_params: Params
}

export type Equipment = EENotCreated | EECreated



export type Experiment = EENotCreated | EECreated

export type CreatedExperiment = Extract<Experiment, { created: true }>



export enum ExperimentStatus {
    NotCreated,
    Stopped,
    Started,
    Paused,
    Completed,
}







export interface Directory {
    files: string[],
    dirs: Record<string, Directory>
}

export type Dependency = {
    id: string
    confirmed: false
} | {
    id: string
    source: DependencySource

    name: string,
    fullname: string,

    confirmed: true
}

export type DependencySource = {
    type: "git",
    git: string,
    subdirectory: string,
    branch: string
} | {
    type: "path",
    path: string,
    editable: boolean
} | {
    type: "pip",
    package: string
} | {
    type: "local",
    directory: string
}