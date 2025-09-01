import z from 'zod';
import { DepartmentsSchema } from '../types/types.js';
import { metMuseumRateLimiter } from '../utils/RateLimiter.js';

export class ListDepartmentsTool {
  public readonly name: string = 'list-departments';
  public readonly description: string = 'List all departments in the Metropolitan Museum of Art (Met Museum)';
  public readonly inputSchema = z.object({}).describe('No input required');

  private readonly apiUrl: string = 'https://collectionapi.metmuseum.org/public/collection/v1/departments';

  public async execute() {
    try {
      const response = await metMuseumRateLimiter.fetch(this.apiUrl);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const jsonData = await response.json();
      const parseResult = DepartmentsSchema.safeParse(jsonData);
      if (!parseResult.success) {
        throw new Error(`Invalid response shape: ${JSON.stringify(parseResult.error.issues, null, 2)}`);
      }
      const text = parseResult.data.departments.map((department) => {
        return `Department ID: ${department.departmentId}, Display Name: ${department.displayName}`;
      }).join('\n');
      return {
        content: [{ type: 'text' as const, text }],
        isError: false,
      };
    }
    catch (error) {
      console.error('Error listing departments:', error);
      return {
        content: [{ type: 'text' as const, text: `Error listing departments: ${error}` }],
        isError: true,
      };
    }
  }
}
