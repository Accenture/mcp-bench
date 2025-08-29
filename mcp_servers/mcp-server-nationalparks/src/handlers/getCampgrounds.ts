import { z } from 'zod';
import { GetCampgroundsSchema } from '../schemas.js';
import { npsApiClient } from '../utils/npsApiClient.js';
import { formatCampgroundData } from '../formatters.js';

export async function getCampgroundsHandler(args: z.infer<typeof GetCampgroundsSchema>) {
  // Set default limit if not provided or if it exceeds maximum
  const limit = args.limit ? Math.min(args.limit, 50) : 10;
  
  // Format the request parameters
  const requestParams = {
    limit,
    ...args
  };
  
  const response = await npsApiClient.getCampgrounds(requestParams);
  
  // Format the response for better readability by the AI
  const formattedCampgrounds = formatCampgroundData(response.data);
  
  // Group campgrounds by park code for better organization
  const campgroundsByPark: { [key: string]: any[] } = {};
  formattedCampgrounds.forEach(campground => {
    if (!campgroundsByPark[campground.parkCode]) {
      campgroundsByPark[campground.parkCode] = [];
    }
    campgroundsByPark[campground.parkCode].push(campground);
  });
  
  const result = {
    total: parseInt(response.total),
    limit: parseInt(response.limit),
    start: parseInt(response.start),
    campgrounds: formattedCampgrounds,
    campgroundsByPark: campgroundsByPark
  };
  
  return {
    content: [{ 
      type: "text", 
      text: JSON.stringify(result, null, 2)
    }]
  };
} 