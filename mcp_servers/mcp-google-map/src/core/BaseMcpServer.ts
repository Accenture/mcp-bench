import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import express, { Request, Response } from "express";
import { Server } from "http";
import { randomUUID } from "node:crypto";
import { Logger } from "../index.js";

const VERSION = "0.0.1";

// Define a structure for tool configurations
export interface ToolConfig {
  name: string;
  description: string;
  schema: any; // Adjust type as per actual SDK (e.g., ZodSchema)
  action: (params: any) => Promise<any>; // Adjust type for params and return
}

export class BaseMcpServer {
  protected readonly server: McpServer;
  private transports: { [sessionId: string]: StreamableHTTPServerTransport } = {};
  private httpServer: Server | null = null;
  private serverName: string;

  constructor(name: string, tools: ToolConfig[]) {
    this.serverName = name;
    this.server = new McpServer(
      {
        name: this.serverName,
        version: VERSION,
      },
      {
        capabilities: {
          logging: {},
          tools: {},
        },
      }
    );

    this.registerTools(tools);
  }

  private registerTools(tools: ToolConfig[]): void {
    tools.forEach((tool) => {
      this.server.tool(tool.name, tool.description, tool.schema, async (params: any) => tool.action(params));
    });
  }

  async connect(transport: Transport): Promise<void> {
    await this.server.connect(transport);

    // Ensure stdout is only used for JSON messages
    const originalStdoutWrite = process.stdout.write.bind(process.stdout);
    process.stdout.write = (chunk: any, encoding?: any, callback?: any) => {
      if (typeof chunk === "string" && !chunk.startsWith("{")) {
        return true; // Silently skip non-JSON messages
      }
      return originalStdoutWrite(chunk, encoding, callback);
    };

    Logger.log(`${this.serverName} connected and ready to process requests`);
  }

  async startHttpServer(port: number): Promise<void> {
    const app = express();
    app.use(express.json());

    // Handle POST requests for client-to-server communication
    app.post("/mcp", async (req: Request, res: Response) => {
      const sessionId = req.headers["mcp-session-id"] as string | undefined;
      let transport: StreamableHTTPServerTransport;

      if (sessionId && this.transports[sessionId]) {
        // Reuse existing transport
        transport = this.transports[sessionId];
      } else if (!sessionId && isInitializeRequest(req.body)) {
        // New initialization request
        transport = new StreamableHTTPServerTransport({
          sessionIdGenerator: () => randomUUID(),
          onsessioninitialized: (sessionId) => {
            this.transports[sessionId] = transport;
            Logger.log(`[${this.serverName}] New session initialized: ${sessionId}`);
          },
          // DNS rebinding protection is disabled by default for backwards compatibility
          // For production use, enable this:
          // enableDnsRebindingProtection: true,
          // allowedHosts: ['127.0.0.1'],
        });

        // Clean up transport when closed
        transport.onclose = () => {
          if (transport.sessionId) {
            delete this.transports[transport.sessionId];
            Logger.log(`[${this.serverName}] Session closed: ${transport.sessionId}`);
          }
        };

        await this.server.connect(transport);
      } else {
        // Invalid request
        res.status(400).json({
          jsonrpc: "2.0",
          error: {
            code: -32000,
            message: "Bad Request: No valid session ID provided",
          },
          id: null,
        });
        return;
      }

      // Handle the request
      await transport.handleRequest(req, res, req.body);
    });

    // Reusable handler for GET and DELETE requests
    const handleSessionRequest = async (req: Request, res: Response) => {
      const sessionId = req.headers["mcp-session-id"] as string | undefined;
      if (!sessionId || !this.transports[sessionId]) {
        res.status(400).send("Invalid or missing session ID");
        return;
      }

      const transport = this.transports[sessionId];
      await transport.handleRequest(req, res);
    };

    // Handle GET requests for server-to-client notifications via SSE
    app.get("/mcp", handleSessionRequest);

    // Handle DELETE requests for session termination
    app.delete("/mcp", handleSessionRequest);

    this.httpServer = app.listen(port, () => {
      Logger.log(`[${this.serverName}] HTTP server listening on port ${port}`);
      Logger.log(`[${this.serverName}] MCP endpoint available at http://localhost:${port}/mcp`);
    });
  }

  async stopHttpServer(): Promise<void> {
    if (!this.httpServer) {
      // Changed to Logger.warn and return, as throwing an error might be too harsh if called multiple times.
      Logger.error(`[${this.serverName}] HTTP server is not running or already stopped.`);
      return;
    }

    return new Promise((resolve, reject) => {
      this.httpServer!.close((err: Error | undefined) => {
        if (err) {
          Logger.error(`[${this.serverName}] Error stopping HTTP server:`, err);
          reject(err);
          return;
        }
        Logger.log(`[${this.serverName}] HTTP server stopped.`);
        this.httpServer = null;
        const closingTransports = Object.values(this.transports).map((transport) => {
          // Clean up transport
          if (transport.sessionId) {
            delete this.transports[transport.sessionId];
          }
          return Promise.resolve();
        });
        Promise.all(closingTransports)
          .then(() => {
            Logger.log(`[${this.serverName}] All transports closed.`);
            resolve();
          })
          .catch((transportCloseErr) => {
            // This catch might be redundant if individual transport close errors are handled
            Logger.error(`[${this.serverName}] Error during bulk transport closing:`, transportCloseErr);
            reject(transportCloseErr);
          });
      });
    });
  }
}
