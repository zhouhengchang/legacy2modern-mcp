#!/usr/bin/env node
/**
 * stdio 入口：本地 IDE 使用（Claude Code / Cursor / Gemini CLI）。
 * token 从环境变量 L2M_TOKEN 读取。
 */
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createServer } from "./src/create-server.js";

const TOKEN = process.env.L2M_TOKEN || "";
const server = createServer(() => TOKEN);
const transport = new StdioServerTransport();
await server.connect(transport);
