import { z } from 'zod';

// Find Parks Schema
export const FindParksSchema = z.object({
  stateCode: z.string().optional().describe('Filter parks by state code (e.g., "CA" for California, "NY" for New York). Multiple states can be comma-separated (e.g., "CA,OR,WA")'),
  q: z.string().optional().describe('Search term to filter parks by name or description'),
  limit: z.number().optional().describe('Maximum number of parks to return (default: 10, max: 50)'),
  start: z.number().optional().describe('Start position for results (useful for pagination)'),
  activities: z.string().optional().describe('Filter by available activities (e.g., "hiking,camping")')
});

// Get Park Details Schema
export const GetParkDetailsSchema = z.object({
  parkCode: z.string().describe('The park code of the national park (e.g., "yose" for Yosemite, "grca" for Grand Canyon)')
});

// Get Alerts Schema
export const GetAlertsSchema = z.object({
  parkCode: z.string().optional().describe('Filter alerts by park code (e.g., "yose" for Yosemite). Multiple parks can be comma-separated (e.g., "yose,grca").'),
  limit: z.number().optional().describe('Maximum number of alerts to return (default: 10, max: 50)'),
  start: z.number().optional().describe('Start position for results (useful for pagination)'),
  q: z.string().optional().describe('Search term to filter alerts by title or description')
});

// Get Visitor Centers Schema
export const GetVisitorCentersSchema = z.object({
  parkCode: z.string().optional().describe('Filter visitor centers by park code (e.g., "yose" for Yosemite). Multiple parks can be comma-separated (e.g., "yose,grca").'),
  limit: z.number().optional().describe('Maximum number of visitor centers to return (default: 10, max: 50)'),
  start: z.number().optional().describe('Start position for results (useful for pagination)'),
  q: z.string().optional().describe('Search term to filter visitor centers by name or description')
});

// Get Campgrounds Schema
export const GetCampgroundsSchema = z.object({
  parkCode: z.string().optional().describe('Filter campgrounds by park code (e.g., "yose" for Yosemite). Multiple parks can be comma-separated (e.g., "yose,grca").'),
  limit: z.number().optional().describe('Maximum number of campgrounds to return (default: 10, max: 50)'),
  start: z.number().optional().describe('Start position for results (useful for pagination)'),
  q: z.string().optional().describe('Search term to filter campgrounds by name or description')
});

// Get Events Schema
export const GetEventsSchema = z.object({
  parkCode: z.string().optional().describe('Filter events by park code (e.g., "yose" for Yosemite). Multiple parks can be comma-separated (e.g., "yose,grca").'),
  limit: z.number().optional().describe('Maximum number of events to return (default: 10, max: 50)'),
  start: z.number().optional().describe('Start position for results (useful for pagination)'),
  dateStart: z.string().optional().describe('Start date for filtering events (format: YYYY-MM-DD)'),
  dateEnd: z.string().optional().describe('End date for filtering events (format: YYYY-MM-DD)'),
  q: z.string().optional().describe('Search term to filter events by title or description')
}); 