/**
 * Сборка MCP-сервера `mcp-swtr` и регистрация инструментов.
 * @module server
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerAllTools } from "./mcp/register.js";

/**
 * Создаёт экземпляр {@link McpServer} с именем `mcp-swtr` и всеми SWTR-инструментами.
 * @returns Подключённый к stdio сервер после `connect(transport)`
 */
export function createServer(): McpServer {
    const server = new McpServer({
        name: "mcp-swtr",
        version: "1.0.0"
    });
    registerAllTools(server);
    return server;
}
