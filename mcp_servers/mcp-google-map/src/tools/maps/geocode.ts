import { z } from "zod";
import { PlacesSearcher } from "../../services/PlacesSearcher.js";

const NAME = "maps_geocode";
const DESCRIPTION = "Convert addresses or place names to geographic coordinates (latitude and longitude)";

const SCHEMA = {
  address: z.string().describe("Address or place name to convert to coordinates"),
};

export type GeocodeParams = z.infer<z.ZodObject<typeof SCHEMA>>;

let placesSearcher: PlacesSearcher | null = null;

async function ACTION(params: GeocodeParams): Promise<{ content: any[]; isError?: boolean }> {
  try {
    if (!placesSearcher) {
      placesSearcher = new PlacesSearcher();
    }
    const result = await placesSearcher.geocode(params.address);

    if (!result.success) {
      return {
        content: [{ type: "text", text: result.error || "地址轉換座標失敗" }],
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
      content: [{ type: "text", text: `地址轉換座標錯誤: ${errorMessage}` }],
    };
  }
}

export const Geocode = {
  NAME,
  DESCRIPTION,
  SCHEMA,
  ACTION,
};