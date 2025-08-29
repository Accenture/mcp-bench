import { z } from 'zod';
import { FindParksSchema } from '../schemas.js';
import { npsApiClient } from '../utils/npsApiClient.js';
import { formatParkData } from '../formatters.js';
import { STATE_CODES } from '../constants.js';

export async function findParksHandler(args: z.infer<typeof FindParksSchema>) {
  // Validate state codes if provided
  if (args.stateCode) {
    const providedStates = args.stateCode.split(',').map(s => s.trim().toUpperCase());
    const invalidStates = providedStates.filter(state => !STATE_CODES.includes(state));
    
    if (invalidStates.length > 0) {
      return {
        content: [{ 
          type: "text", 
          text: JSON.stringify({
            error: `Invalid state code(s): ${invalidStates.join(', ')}`,
            validStateCodes: STATE_CODES
          })
        }]
      };
    }
  }
  
  // Set default limit if not provided or if it exceeds maximum
  const limit = args.limit ? Math.min(args.limit, 50) : 10;
  
  // Format the request parameters
  const requestParams = {
    limit,
    ...args
  };
  
  const response = await npsApiClient.getParks(requestParams);
  
  // Format the response for better readability by the AI
  const formattedParks = formatParkData(response.data);
  
  const result = {
    total: parseInt(response.total),
    limit: parseInt(response.limit),
    start: parseInt(response.start),
    parks: formattedParks
  };
  
  return {
    content: [{ 
      type: "text", 
      text: JSON.stringify(result, null, 2)
    }]
  };
} 