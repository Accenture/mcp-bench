import { z } from "zod";
import { PlacesSearcher } from "../../services/PlacesSearcher.js";

const NAME = "maps_reverse_geocode";
const DESCRIPTION = "Convert geographic coordinates (latitude and longitude) to a human-readable address";

const SCHEMA = {
  latitude: z.number().describe("Latitude coordinate"),
  longitude: z.number().describe("Longitude coordinate"),
};

export type ReverseGeocodeParams = z.infer<z.ZodObject<typeof SCHEMA>>;

let placesSearcher: PlacesSearcher | null = null;

async function ACTION(params: ReverseGeocodeParams): Promise<{ content: any[]; isError?: boolean }> {
  try {
    if (!placesSearcher) {
      placesSearcher = new PlacesSearcher();
    }
    const result = await placesSearcher.reverseGeocode(params.latitude, params.longitude);

    if (!result.success) {
      return {
        content: [{ type: "text", text: result.error || "座標轉換地址失敗" }],
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
      content: [{ type: "text", text: `座標轉換地址錯誤: ${errorMessage}` }],
    };
  }
}

export const ReverseGeocode = {
  NAME,
  DESCRIPTION,
  SCHEMA,
  ACTION,
};