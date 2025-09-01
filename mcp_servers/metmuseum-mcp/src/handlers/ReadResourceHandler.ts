import type { ReadResourceRequest } from '@modelcontextprotocol/sdk/types.js';
import type { GetObjectTool } from '../tools/GetObjectTool.js';

export class ReadResourceHandler {
  private getObjectTool: GetObjectTool;

  constructor(getObjectTool: GetObjectTool) {
    this.getObjectTool = getObjectTool;
  }

  public async handleReadResource(request: ReadResourceRequest) {
    const uri = request.params.uri;
    if (uri.startsWith('met-image://')) {
      const title = uri.split('://')[1];
      const image = this.getObjectTool.imageByTitle.get(title);
      if (image) {
        return {
          contents: [{
            uri,
            mimeType: 'image/jpeg',
            blob: image,
          }],
        };
      }
    }
    return {
      content: [{ type: 'text', text: `Resource not found: ${uri}` }],
      isError: true,
    };
  }
}
