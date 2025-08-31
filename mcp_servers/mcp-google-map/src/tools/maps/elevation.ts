import { z } from "zod";
import { PlacesSearcher } from "../../services/PlacesSearcher.js";

const NAME = "maps_elevation";
const DESCRIPTION = "Get elevation data (height above sea level) for specific geographic locations";

const SCHEMA = {
  locations: z.array(z.object({
    latitude: z.number().describe("Latitude coordinate"),
    longitude: z.number().describe("Longitude coordinate"),
  })).describe("List of locations to get elevation data for"),
};

export type ElevationParams = z.infer<z.ZodObject<typeof SCHEMA>>;

let placesSearcher: PlacesSearcher | null = null;

async function ACTION(params: ElevationParams): Promise<{ content: any[]; isError?: boolean }> {
  try {
    if (!placesSearcher) {
      placesSearcher = new PlacesSearcher();
    }
    const result = await placesSearcher.getElevation(params.locations);

    if (!result.success) {
      return {
        content: [{ type: "text", text: result.error || "獲取海拔數據失敗" }],
        isError: true,
      };
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result.data, null, 2),
        },
      ],
      isError: false,
    };
  } catch (error: any) {
    const errorMessage = error instanceof Error ? error.message : JSON.stringify(error);
    return {
      isError: true,
      content: [{ type: "text", text: `獲取海拔數據錯誤: ${errorMessage}` }],
    };
  }
}

export const Elevation = {
  NAME,
  DESCRIPTION,
  SCHEMA,
  ACTION,
};