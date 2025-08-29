import { z } from 'zod';
import { GetEventsSchema } from '../schemas.js';
import { npsApiClient } from '../utils/npsApiClient.js';
import { formatEventData } from '../formatters.js';

export async function getEventsHandler(args: z.infer<typeof GetEventsSchema>) {
  // Set default limit if not provided or if it exceeds maximum
  const limit = args.limit ? Math.min(args.limit, 50) : 10;
  
  // Format the request parameters
  const requestParams = {
    limit,
    ...args
  };
  
  const response = await npsApiClient.getEvents(requestParams);
  
  // Format the response for better readability by the AI
  const formattedEvents = formatEventData(response.data);
  
  // Group events by park code for better organization
  const eventsByPark: { [key: string]: any[] } = {};
  formattedEvents.forEach(event => {
    if (!eventsByPark[event.parkCode]) {
      eventsByPark[event.parkCode] = [];
    }
    eventsByPark[event.parkCode].push(event);
  });
  
  const result = {
    total: parseInt(response.total),
    limit: parseInt(response.limit),
    start: parseInt(response.start),
    events: formattedEvents,
    eventsByPark: eventsByPark
  };
  
  return {
    content: [{ 
      type: "text", 
      text: JSON.stringify(result, null, 2)
    }]
  };
} 