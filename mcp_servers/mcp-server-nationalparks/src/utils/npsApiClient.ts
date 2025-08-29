/**
 * NPS API Client
 * 
 * A client for interacting with the National Park Service API.
 * https://www.nps.gov/subjects/developer/api-documentation.htm
 */

import axios, { AxiosInstance } from 'axios';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Define types for API responses
export interface NPSResponse<T> {
  total: string;
  limit: string;
  start: string;
  data: T[];
}

export interface ParkData {
  id: string;
  url: string;
  fullName: string;
  parkCode: string;
  description: string;
  latitude: string;
  longitude: string;
  latLong: string;
  activities: Array<{ id: string; name: string }>;
  topics: Array<{ id: string; name: string }>;
  states: string;
  contacts: {
    phoneNumbers: Array<{ phoneNumber: string; description: string; extension: string; type: string }>;
    emailAddresses: Array<{ description: string; emailAddress: string }>;
  };
  entranceFees: Array<{ cost: string; description: string; title: string }>;
  entrancePasses: Array<{ cost: string; description: string; title: string }>;
  fees: any[];
  directionsInfo: string;
  directionsUrl: string;
  operatingHours: Array<{
    exceptions: any[];
    description: string;
    standardHours: {
      sunday: string;
      monday: string;
      tuesday: string;
      wednesday: string;
      thursday: string;
      friday: string;
      saturday: string;
    };
    name: string;
  }>;
  addresses: Array<{
    postalCode: string;
    city: string;
    stateCode: string;
    line1: string;
    line2: string;
    line3: string;
    type: string;
  }>;
  images: Array<{
    credit: string;
    title: string;
    altText: string;
    caption: string;
    url: string;
  }>;
  weatherInfo: string;
  name: string;
  designation: string;
}

export interface AlertData {
  id: string;
  url: string;
  title: string;
  parkCode: string;
  description: string;
  category: string;
  lastIndexedDate: string;
}

// Define parameter types for the API methods
export interface ParkQueryParams {
  parkCode?: string;
  stateCode?: string;
  limit?: number;
  start?: number;
  q?: string;
  fields?: string;
}

export interface AlertQueryParams {
  parkCode?: string;
  limit?: number;
  start?: number;
  q?: string;
}

export interface VisitorCenterData {
  id: string;
  url: string;
  name: string;
  parkCode: string;
  description: string;
  latitude: string;
  longitude: string;
  latLong: string;
  directionsInfo: string;
  directionsUrl: string;
  addresses: Array<{
    postalCode: string;
    city: string;
    stateCode: string;
    line1: string;
    line2: string;
    line3: string;
    type: string;
  }>;
  operatingHours: Array<{
    exceptions: any[];
    description: string;
    standardHours: {
      sunday: string;
      monday: string;
      tuesday: string;
      wednesday: string;
      thursday: string;
      friday: string;
      saturday: string;
    };
    name: string;
  }>;
  contacts: {
    phoneNumbers: Array<{ phoneNumber: string; description: string; extension: string; type: string }>;
    emailAddresses: Array<{ description: string; emailAddress: string }>;
  };
}

export interface CampgroundData {
  id: string;
  url: string;
  name: string;
  parkCode: string;
  description: string;
  latitude: string;
  longitude: string;
  latLong: string;
  audioDescription: string;
  isPassportStampLocation: boolean;
  passportStampLocationDescription: string;
  passportStampImages: any[];
  geometryPoiId: string;
  reservationInfo: string;
  reservationUrl: string;
  regulationsurl: string;
  regulationsOverview: string;
  amenities: {
    trashRecyclingCollection: boolean;
    toilets: string[];
    internetConnectivity: boolean;
    showers: string[];
    cellPhoneReception: boolean;
    laundry: boolean;
    amphitheater: boolean;
    dumpStation: boolean;
    campStore: boolean;
    staffOrVolunteerHostOnsite: boolean;
    potableWater: string[];
    iceAvailableForSale: boolean;
    firewoodForSale: boolean;
    foodStorageLockers: boolean;
  };
  contacts: {
    phoneNumbers: Array<{ phoneNumber: string; description: string; extension: string; type: string }>;
    emailAddresses: Array<{ description: string; emailAddress: string }>;
  };
  fees: Array<{
    cost: string;
    description: string;
    title: string;
  }>;
  directionsOverview: string;
  directionsUrl: string;
  operatingHours: Array<{
    exceptions: any[];
    description: string;
    standardHours: {
      sunday: string;
      monday: string;
      tuesday: string;
      wednesday: string;
      thursday: string;
      friday: string;
      saturday: string;
    };
    name: string;
  }>;
  addresses: Array<{
    postalCode: string;
    city: string;
    stateCode: string;
    line1: string;
    line2: string;
    line3: string;
    type: string;
  }>;
  weatherOverview: string;
  numberOfSitesReservable: string;
  numberOfSitesFirstComeFirstServe: string;
  campsites: {
    totalSites: string;
    group: string;
    horse: string;
    tentOnly: string;
    electricalHookups: string;
    rvOnly: string;
    walkBoatTo: string;
    other: string;
  };
  accessibility: {
    wheelchairAccess: string;
    internetInfo: string;
    cellPhoneInfo: string;
    fireStovePolicy: string;
    rvAllowed: boolean;
    rvInfo: string;
    rvMaxLength: string;
    additionalInfo: string;
    trailerMaxLength: string;
    adaInfo: string;
    trailerAllowed: boolean;
    accessRoads: string[];
    classifications: string[];
  };
}

export interface EventData {
  id: string;
  url: string;
  title: string;
  parkFullName: string;
  description: string;
  latitude: string;
  longitude: string;
  category: string;
  subcategory: string;
  location: string;
  tags: string[];
  recurrenceDateStart: string;
  recurrenceDateEnd: string;
  times: Array<{
    timeStart: string;
    timeEnd: string;
    sunriseTimeStart: boolean;
    sunsetTimeEnd: boolean;
  }>;
  dates: string[];
  dateStart: string;
  dateEnd: string;
  regresurl: string;
  contactEmailAddress: string;
  contactTelephoneNumber: string;
  feeInfo: string;
  isRecurring: boolean;
  isAllDay: boolean;
  siteCode: string;
  parkCode: string;
  organizationName: string;
  types: string[];
  createDate: string;
  lastUpdated: string;
  infoURL: string;
  portalName: string;
}

export interface VisitorCenterQueryParams {
  parkCode?: string;
  limit?: number;
  start?: number;
  q?: string;
}

export interface CampgroundQueryParams {
  parkCode?: string;
  limit?: number;
  start?: number;
  q?: string;
}

export interface EventQueryParams {
  parkCode?: string;
  limit?: number;
  start?: number;
  q?: string;
  dateStart?: string;
  dateEnd?: string;
}

/**
 * NPS API Client class
 */
class NPSApiClient {
  private api: AxiosInstance;
  private baseUrl: string = 'https://developer.nps.gov/api/v1';
  private apiKey: string;

  constructor() {
    this.apiKey = process.env.NPS_API_KEY || '';
    
    if (!this.apiKey) {
      console.warn('Warning: NPS_API_KEY is not set in environment variables.');
      console.warn('Get your API key at: https://www.nps.gov/subjects/developer/get-started.htm');
    }
    
    // Create axios instance for NPS API
    this.api = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'X-Api-Key': this.apiKey,
      },
    });

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          // Check for rate limiting
          if (error.response.status === 429) {
            console.error('Rate limit exceeded for NPS API. Please try again later.');
          }
          
          // Log the error details
          console.error('NPS API Error:', {
            status: error.response.status,
            statusText: error.response.statusText,
            data: error.response.data,
          });
        } else if (error.request) {
          console.error('No response received from NPS API:', error.request);
        } else {
          console.error('Error setting up NPS API request:', error.message);
        }
        
        return Promise.reject(error);
      }
    );
  }

  /**
   * Fetch parks data from the NPS API
   * @param params Query parameters
   * @returns Promise with parks data
   */
  async getParks(params: ParkQueryParams = {}): Promise<NPSResponse<ParkData>> {
    try {
      const response = await this.api.get('/parks', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching parks data:', error);
      throw error;
    }
  }

  /**
   * Fetch a specific park by its parkCode
   * @param parkCode The park code (e.g., 'yose' for Yosemite)
   * @returns Promise with the park data
   */
  async getParkByCode(parkCode: string): Promise<NPSResponse<ParkData>> {
    try {
      const response = await this.api.get('/parks', { 
        params: { 
          parkCode,
          limit: 1
        } 
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching park with code ${parkCode}:`, error);
      throw error;
    }
  }

  /**
   * Fetch alerts from the NPS API
   * @param params Query parameters
   * @returns Promise with alerts data
   */
  async getAlerts(params: AlertQueryParams = {}): Promise<NPSResponse<AlertData>> {
    try {
      const response = await this.api.get('/alerts', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching alerts data:', error);
      throw error;
    }
  }

  /**
   * Fetch alerts for a specific park
   * @param parkCode The park code (e.g., 'yose' for Yosemite)
   * @returns Promise with the park's alerts
   */
  async getAlertsByParkCode(parkCode: string): Promise<NPSResponse<AlertData>> {
    try {
      const response = await this.api.get('/alerts', { 
        params: { 
          parkCode 
        } 
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching alerts for park ${parkCode}:`, error);
      throw error;
    }
  }

  /**
   * Fetch visitor centers from the NPS API
   * @param params Query parameters
   * @returns Promise with visitor centers data
   */
  async getVisitorCenters(params: VisitorCenterQueryParams = {}): Promise<NPSResponse<VisitorCenterData>> {
    try {
      const response = await this.api.get('/visitorcenters', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching visitor centers data:', error);
      throw error;
    }
  }

  /**
   * Fetch campgrounds from the NPS API
   * @param params Query parameters
   * @returns Promise with campgrounds data
   */
  async getCampgrounds(params: CampgroundQueryParams = {}): Promise<NPSResponse<CampgroundData>> {
    try {
      const response = await this.api.get('/campgrounds', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching campgrounds data:', error);
      throw error;
    }
  }

  /**
   * Fetch events from the NPS API
   * @param params Query parameters
   * @returns Promise with events data
   */
  async getEvents(params: EventQueryParams = {}): Promise<NPSResponse<EventData>> {
    try {
      const response = await this.api.get('/events', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching events data:', error);
      throw error;
    }
  }
}

// Export a singleton instance
export const npsApiClient = new NPSApiClient();