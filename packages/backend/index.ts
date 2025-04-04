import { $, file, serve, type RouterTypes } from "bun"
import { headers } from "./lib/_shared";
import { app_state, postCli } from "./lib/app_state";
import { copyApp, initiateWorkspace, loadWorkspace, readAllUvDependencies, runProject, saveWorkspace, shell } from "./lib/workspace";
import { pathExist } from "./lib/fs";
import { mkdir } from "node:fs/promises"

function consoleIterator(...data: any[]) {

    postCli("backend", typeof data[0] === "string" ? data[0] : JSON.stringify(data[0]))
}

console.log = consoleIterator




serve({
    port: 4000,
    hostname: "localhost",
    websocket: {
        open(ws) {

            app_state.ws = ws

            // Post all accumulated logs to the frontend
            if (app_state.logs.length > 0) {
                const logs = JSON.parse(JSON.stringify(app_state.logs))
                app_state.logs = []

                ws.send(JSON.stringify({ logs }))


            }
        },
        message(ws, message) {
            // The websocket is only used to post logs to the frontend. As such there is no message handler
        },
        close(ws) {
            app_state.ws = undefined
        }

    },
    routes: {
        "/workspace/load": {
            POST: async req => {
                const { path } = await req.json() as { path: string }

                const path_exist = await pathExist(path)

                if (!path_exist) {
                    await mkdir(path)
                    await initiateWorkspace(path)
                }

                if (!await pathExist(path + "/app"))
                    await copyApp(path)

                await runProject(path)
                return Response.json(await loadWorkspace(path), { headers })
            }
        }
        ,
        "/workspace/save": {
            POST: async req => {
                const { path, payload } = await req.json() as { path: string, payload: any }
                await saveWorkspace(path, payload)
                return Response.json({}, { headers })
            }
        }
        ,
        "/workspace/dependency/check_init": {
            POST: async req => {
                const { path, directory } = await req.json() as { directory: string, path: string }
                return Response.json({ success: await file(path + "/" + directory + "/__init__.py").exists() }, { headers })
            }
        },
        "/workspace/dependency/add": {
            POST: async req => {
                const { path, source } = await req.json() as { source: string, path: string }

                // Could be from pip, git path or local path
                shell(`uv add ${{ raw: source }}`, path)
                return Response.json({}, { headers })
            }
        },
        "/workspace/dependency/remove": {
            POST: async req => {
                const { path, name } = await req.json() as { name: string, path: string }

                shell(`uv remove ${name}`, path)
                return Response.json({}, { headers })
            }
        },
        "/workspace/dependency/read_all": {
            POST: async req => {
                const { path } = await req.json() as { path: string }
                return Response.json(await readAllUvDependencies(path), { headers })
            }
        },
        "/workspace/disconnect": {
            GET: async req => {
                if (app_state.pyproc === undefined) {
                    console.log("disconnection successful")
                    return Response.json({ "success": true }, { headers })
                }

                if (app_state.pyproc !== undefined) {
                    const res = await (await fetch("http://localhost:8000/workspace/forcestop")).json() as { success: boolean }
                    if (res.success) {
                        app_state.pyproc?.kill()
                        // wait for 100 ms
                        await new Promise(_ => setTimeout(_, 1000));
                        console.log("disconnection successful")
                        return Response.json({ "success": true }, { headers })
                    }
                }
                console.log("disconnection failed")
                return Response.json({ "success": false }, { headers })
            }
        }
    },
    async fetch(req, server) {

        // Handle CORS preflight requests
        if (req.method === 'OPTIONS')
            return new Response('', { headers });



        // Upgrade to websocket
        if (new URL(req.url).pathname === "/cli" && server.upgrade(req)) {

            return undefined as unknown as Response; // do not return a Response
        }


        return new Response('Not Found', { headers, status: 404 });
    },

});



process.on("SIGINT", async () => {

    if (app_state.pyproc !== undefined) {

        const res = await fetch("http://localhost:8000/workspace/forcestop")
        console.log(await res.json())
        app_state.pyproc?.kill()
        // wait for 100 ms
        await new Promise(_ => setTimeout(_, 1000));
    }

    process.exit();
});