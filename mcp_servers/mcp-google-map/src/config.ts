import { ToolConfig } from "./core/BaseMcpServer.js";

// Import tool definitions
import { SearchNearby, SearchNearbyParams } from "./tools/maps/searchNearby.js";
import { PlaceDetails, PlaceDetailsParams } from "./tools/maps/placeDetails.js";
import { Geocode, GeocodeParams } from "./tools/maps/geocode.js";
import { ReverseGeocode, ReverseGeocodeParams } from "./tools/maps/reverseGeocode.js";
import { DistanceMatrix, DistanceMatrixParams } from "./tools/maps/distanceMatrix.js";
import { Directions, DirectionsParams } from "./tools/maps/directions.js";
import { Elevation, ElevationParams } from "./tools/maps/elevation.js";
interface ServerInstanceConfig {
  // Renamed from ServerConfig and modified
  name: string;
  portEnvVar: string;
  tools: ToolConfig[];
}

const serverConfigs: ServerInstanceConfig[] = [
  {
    name: "MCP-Server",
    portEnvVar: "MCP_SERVER_PORT",
    tools: [
      {
        name: SearchNearby.NAME,
        description: SearchNearby.DESCRIPTION,
        schema: SearchNearby.SCHEMA,
        action: (params: SearchNearbyParams) => SearchNearby.ACTION(params),
      },
      {
        name: PlaceDetails.NAME,
        description: PlaceDetails.DESCRIPTION,
        schema: PlaceDetails.SCHEMA,
        action: (params: PlaceDetailsParams) => PlaceDetails.ACTION(params),
      },
      {
        name: Geocode.NAME,
        description: Geocode.DESCRIPTION,
        schema: Geocode.SCHEMA,
        action: (params: GeocodeParams) => Geocode.ACTION(params),
      },
      {
        name: ReverseGeocode.NAME,
        description: ReverseGeocode.DESCRIPTION,
        schema: ReverseGeocode.SCHEMA,
        action: (params: ReverseGeocodeParams) => ReverseGeocode.ACTION(params),
      },
      {
        name: DistanceMatrix.NAME,
        description: DistanceMatrix.DESCRIPTION,
        schema: DistanceMatrix.SCHEMA,
        action: (params: DistanceMatrixParams) => DistanceMatrix.ACTION(params),
      },
      {
        name: Directions.NAME,
        description: Directions.DESCRIPTION,
        schema: Directions.SCHEMA,
        action: (params: DirectionsParams) => Directions.ACTION(params),
      },
      {
        name: Elevation.NAME,
        description: Elevation.DESCRIPTION,
        schema: Elevation.SCHEMA,
        action: (params: ElevationParams) => Elevation.ACTION(params),
      },
    ],
  },
];

export default serverConfigs;
