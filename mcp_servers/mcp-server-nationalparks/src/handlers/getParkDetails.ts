import { z } from 'zod';
import { GetParkDetailsSchema } from '../schemas.js';
import { npsApiClient } from '../utils/npsApiClient.js';
import { formatParkDetails } from '../formatters.js';

export async function getParkDetailsHandler(args: z.infer<typeof GetParkDetailsSchema>) {
  const response = await npsApiClient.getParkByCode(args.parkCode);
  
  // Check if park was found
  if (!response.data || response.data.length === 0) {
    return {
      content: [{ 
        type: "text", 
        text: JSON.stringify({
          error: 'Park not found',
          message: `No park found with park code: ${args.parkCode}`
        }, null, 2)
      }]
    };
  }
  
  // Format the response for better readability by the AI
  const parkDetails = formatParkDetails(response.data[0]);
  
  return {
    content: [{ 
      type: "text", 
      text: JSON.stringify(parkDetails, null, 2)
    }]
  };
} 