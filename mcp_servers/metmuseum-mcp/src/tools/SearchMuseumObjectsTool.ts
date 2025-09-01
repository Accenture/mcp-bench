import z from 'zod';
import { SearchResponseSchema } from '../types/types.js';
import { metMuseumRateLimiter } from '../utils/RateLimiter.js';

/**
 * Tool for searching objects in the Met Museum
 */
export class SearchMuseumObjectsTool {
  // Define public tool properties
  public readonly name: string = 'search-museum-objects';
  public readonly description: string = 'Search for objects in the Metropolitan Museum of Art (Met Museum). Will return Total objects found, '
    + 'followed by a list of Object Ids.'
    + 'The parameter title should be set to true if you want to search for objects by title.'
    + 'The parameter hasImages is false by default, but can be set to true to return objects without images.'
    + 'If the parameter hasImages is true, the parameter title should be false.';

  // Define the input schema
  public readonly inputSchema = z.object({
    q: z.string().describe(`The search query, Returns a listing of all Object IDs for objects that contain the search query within the object's data`),
    hasImages: z.boolean().optional().default(false).describe(`Only returns objects that have images`),
    title: z.boolean().optional().default(false).describe(`This should be set to true if you want to search for objects by title`),
    departmentId: z.number().optional().describe(`Returns objects that are in the specified department. The departmentId should come from the 'list-departments' tool.`),
  });

  // Type for input parameters
  private readonly apiBaseUrl: string = 'https://collectionapi.metmuseum.org/public/collection/v1/search';

  /**
   * Execute the search operation
   */
  public async execute({ q, hasImages, title, departmentId }: z.infer<typeof this.inputSchema>) {
    try {
      const url = new URL(this.apiBaseUrl);
      url.searchParams.set('q', q);
      if (hasImages) {
        url.searchParams.set('hasImages', 'true');
      }
      if (title && !hasImages) {
        url.searchParams.set('title', 'true');
      }
      if (departmentId) {
        url.searchParams.set('departmentId', departmentId.toString());
      }

      const response = await metMuseumRateLimiter.fetch(url.toString());
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const jsonData = await response.json();
      const parseResult = SearchResponseSchema.safeParse(jsonData);

      if (!parseResult.success) {
        throw new Error(`Invalid response shape: ${JSON.stringify(parseResult.error.issues, null, 2)}`);
      }

      if (parseResult.data.total === 0 || !parseResult.data.objectIDs) {
        return {
          content: [{ type: 'text' as const, text: 'No objects found' }],
          isError: false,
        };
      }

      const text = `Total objects found: ${parseResult.data.total}\nObject IDs: ${parseResult.data.objectIDs.join(', ')}`;
      return {
        content: [{ type: 'text' as const, text }],
        isError: false,
      };
    }
    catch (error) {
      console.error('Error searching museum objects:', error);
      return {
        content: [{ type: 'text' as const, text: `Error searching museum objects: ${error}` }],
        isError: true,
      };
    }
  }
}

export const SearchInputSchema = new SearchMuseumObjectsTool().inputSchema;
