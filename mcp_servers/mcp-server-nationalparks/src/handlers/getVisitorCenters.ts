import { z } from 'zod';
import { GetVisitorCentersSchema } from '../schemas.js';
import { npsApiClient } from '../utils/npsApiClient.js';
import { formatVisitorCenterData } from '../formatters.js';

export async function getVisitorCentersHandler(args: z.infer<typeof GetVisitorCentersSchema>) {
  // Set default limit if not provided or if it exceeds maximum
  const limit = args.limit ? Math.min(args.limit, 50) : 10;
  
  // Format the request parameters
  const requestParams = {
    limit,
    ...args
  };
  
  const response = await npsApiClient.getVisitorCenters(requestParams);
  
  // Format the response for better readability by the AI
  const formattedCenters = formatVisitorCenterData(response.data);
  
  // Group visitor centers by park code for better organization
  const centersByPark: { [key: string]: any[] } = {};
  formattedCenters.forEach(center => {
    if (!centersByPark[center.parkCode]) {
      centersByPark[center.parkCode] = [];
    }
    centersByPark[center.parkCode].push(center);
  });
  
  const result = {
    total: parseInt(response.total),
    limit: parseInt(response.limit),
    start: parseInt(response.start),
    visitorCenters: formattedCenters,
    visitorCentersByPark: centersByPark
  };
  
  return {
    content: [{ 
      type: "text", 
      text: JSON.stringify(result, null, 2)
    }]
  };
} 