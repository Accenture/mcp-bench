import type { GetObjectTool } from '../tools/GetObjectTool.js';

export class ListResourcesHandler {
  private getObjectTool: GetObjectTool;

  constructor(getObjectTool: GetObjectTool) {
    this.getObjectTool = getObjectTool;
  }

  public async handleListResources() {
    return {
      resources: [
        ...Array.from(this.getObjectTool.imageByTitle.keys()).map(title => ({
          uri: `met-image://${title}`,
          mimeType: 'image/png',
          name: `${title}`,
        })),
      ],
    };
  }
}
