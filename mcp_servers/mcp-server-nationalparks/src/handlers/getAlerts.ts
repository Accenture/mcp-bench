import { z } from 'zod';
import { GetAlertsSchema } from '../schemas.js';
import { npsApiClient } from '../utils/npsApiClient.js';
import { formatAlertData } from '../formatters.js';

export async function getAlertsHandler(args: z.infer<typeof GetAlertsSchema>) {
  // Set default limit if not provided or if it exceeds maximum
  const limit = args.limit ? Math.min(args.limit, 50) : 10;
  
  // Format the request parameters
  const requestParams = {
    limit,
    ...args
  };
  
  const response = await npsApiClient.getAlerts(requestParams);
  
  // Format the response for better readability by the AI
  const formattedAlerts = formatAlertData(response.data);
  
  // Group alerts by park code for better organization
  const alertsByPark: { [key: string]: any[] } = {};
  formattedAlerts.forEach(alert => {
    if (!alertsByPark[alert.parkCode]) {
      alertsByPark[alert.parkCode] = [];
    }
    alertsByPark[alert.parkCode].push(alert);
  });
  
  const result = {
    total: parseInt(response.total),
    limit: parseInt(response.limit),
    start: parseInt(response.start),
    alerts: formattedAlerts,
    alertsByPark
  };
  
  return {
    content: [{ 
      type: "text", 
      text: JSON.stringify(result, null, 2)
    }]
  };
} 