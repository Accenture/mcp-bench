import { z } from "zod";
import { PlacesSearcher } from "../../services/PlacesSearcher.js";

const NAME = "maps_distance_matrix";
const DESCRIPTION = "Calculate travel distances and durations between multiple origins and destinations for different travel modes";

const SCHEMA = {
  origins: z.array(z.string()).describe("List of origin addresses or coordinates"),
  destinations: z.array(z.string()).describe("List of destination addresses or coordinates"),
  mode: z.enum(["driving", "walking", "bicycling", "transit"]).default("driving").describe("Travel mode for calculation"),
};

export type DistanceMatrixParams = z.infer<z.ZodObject<typeof SCHEMA>>;

let placesSearcher: PlacesSearcher | null = null;

async function ACTION(params: DistanceMatrixParams): Promise<{ content: any[]; isError?: boolean }> {
  try {
    if (!placesSearcher) {
      placesSearcher = new PlacesSearcher();
    }
    const result = await placesSearcher.calculateDistanceMatrix(params.origins, params.destinations, params.mode);

    if (!result.success) {
      return {
        content: [{ type: "text", text: result.error || "計算距離矩陣失敗" }],
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
      content: [{ type: "text", text: `計算距離矩陣錯誤: ${errorMessage}` }],
    };
  }
}

export const DistanceMatrix = {
  NAME,
  DESCRIPTION,
  SCHEMA,
  ACTION,
};