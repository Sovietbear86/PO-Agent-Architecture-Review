/**
 * Точка входа npx-пакета: MCP-сервер SWTR по stdio.
 * @module index
 */

import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createServer } from "./server.js";

/** Отключаем проверку TLS (аналог Python `verify=False`) */
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

/** Лог-файл в домашней директории пользователя */
const LOG_FILE = path.join(os.homedir(), ".mcp-swtr.log");

/**
 * Пишет строку в лог-файл (stderr нельзя — может нарушить stdio-протокол MCP).
 */
function log(level: "INFO" | "ERROR" | "WARN", message: string, err?: unknown): void {
    const ts = new Date().toISOString();
    const errStr =
        err instanceof Error ? ` | ${err.message}\n${err.stack}` : err ? ` | ${String(err)}` : "";
    const line = `[${ts}] [${level}] ${message}${errStr}\n`;
    try {
        fs.appendFileSync(LOG_FILE, line);
    } catch {
        // если не можем писать в лог — молчим, не роняем процесс
    }
}

/** Ловим необработанные исключения — иначе процесс падает молча */
process.on("uncaughtException", (err) => {
    log("ERROR", "uncaughtException", err);
    process.exit(1);
});

process.on("unhandledRejection", (reason) => {
    log("ERROR", "unhandledRejection", reason);
    // не выходим — MCP SDK сам разберётся с ошибками tool-handlers
});

/**
 * Поднимает MCP-сервер и блокируется на stdio-транспорте.
 */
async function main(): Promise<void> {
    log("INFO", `mcp-swtr starting, pid=${process.pid}`);
    const server = createServer();
    const transport = new StdioServerTransport();
    await server.connect(transport);
    log("INFO", "mcp-swtr connected");
}

main().catch((err) => {
    log("ERROR", "main() crashed", err);
    process.exit(1);
});
