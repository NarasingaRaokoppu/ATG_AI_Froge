import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";
// https://vitejs.dev/config/
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, ".", "");
    return {
        plugins: [react()],
        server: {
            port: 5173,
        },
        define: {
            "import.meta.env.VITE_API_URL": JSON.stringify(env.VITE_API_URL || "http://localhost:8000/api"),
        },
    };
});
