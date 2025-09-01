import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import imageToBase64 from 'image-to-base64';
import z from 'zod';
import { ObjectResponseSchema } from '../types/types.js';
import { metMuseumRateLimiter } from '../utils/RateLimiter.js';

export class GetObjectTool {
  public readonly name: string = 'get-museum-object';
  public readonly description: string = 'Get a museum object by its ID, from the Metropolitan Museum of Art Collection';
  public readonly inputSchema = z.object({
    objectId: z.number().describe('The ID of the museum object to retrieve'),
    returnImage: z.boolean().optional().default(true).describe('Whether to return the image (if available) of the object and add it to the server resources'),
  }).describe('Get a museum object by its ID');

  public readonly imageByTitle = new Map<string, string>();

  private readonly baseURL: string = 'https://collectionapi.metmuseum.org/public/collection/v1/objects/';

  private readonly server: McpServer;

  constructor(server: McpServer) {
    this.server = server;
  }

  public async execute({ objectId, returnImage }: z.infer<typeof this.inputSchema>) {
    try {
      const url = `${this.baseURL}${objectId}`;
      const response = await metMuseumRateLimiter.fetch(url.toString());
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const jsonData = await response.json();
      const parseResult = ObjectResponseSchema.safeParse(jsonData);
      if (!parseResult.success) {
        throw new Error(`Invalid response shape: ${JSON.stringify(parseResult.error.issues, null, 2)}`);
      }
      const data = parseResult.data;
      const text = `Title: ${data.title}\n`
        + `${data.artistDisplayName ? `Artist: ${data.artistDisplayName}\n` : ''}`
        + `${data.artistDisplayBio ? `Artist Bio: ${data.artistDisplayBio}\n` : ''}`
        + `${data.department ? `Department: ${data.department}\n` : ''}`
        + `${data.creditLine ? `Credit Line: ${data.creditLine}\n` : ''}`
        + `${data.medium ? `Medium: ${data.medium}\n` : ''}`
        + `${data.dimensions ? `Dimensions: ${data.dimensions}\n` : ''}`
        + `${data.primaryImage ? `Primary Image URL: ${data.primaryImage}\n` : ''}`
        + `${data.tags ? `Tags: ${data.tags.map(tag => tag.term).join(', ')}\n` : ''}`;

      const content = [];
      content.push({
        type: 'text' as const,
        text,
      });
      if (returnImage && data.primaryImageSmall) {
        const imageBase64 = await imageToBase64(data.primaryImageSmall);
        content.push({
          type: 'image' as const,
          data: imageBase64,
          mimeType: 'image/jpeg',
        });
        this.imageByTitle.set(data.title!, imageBase64);
        this.server.server.notification({
          method: 'notifications/resources/list_changed',
        });
      }

      return { content };
    }
    catch (error) {
      console.error('Error getting museum object:', error);
      return {
        content: [{ type: 'text' as const, text: `Error getting museum object id ${objectId}: ${error}` }],
        isError: true,
      };
    }
  }
}
