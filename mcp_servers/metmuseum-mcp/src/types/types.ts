import z from 'zod';

/**
 * https://metmuseum.github.io/#departments
 */
const DepartmentSchema = z.object({
  departmentId: z.number().describe(
    'Department ID as an integer. The departmentId is to be used as a query '
    + 'parameter on the `/objects` endpoint',
  ),
  displayName: z.string().describe('Display name for a department'),
});

export const DepartmentsSchema = z.object({
  departments: z.array(DepartmentSchema).describe(
    'An array containing the JSON objects that contain each department\'s '
    + 'departmentId and display name. The departmentId is to be used as a '
    + 'query parameter on the `/objects` endpoint',
  ),
});

export const SearchResponseSchema = z.object({
  total: z.number().describe(
    'The total number of publicly-available objects',
  ),
  objectIDs: z.array(z.number()).nullable().describe(
    'An array containing the object ID of publicly-available object',
  ),
});

const constituentSchema = z.object({
  constituentID: z.number(),
  role: z.string(),
  name: z.string(),
  constituentULAN_URL: z.string(),
  constituentWikidata_URL: z.string(),
  gender: z.string(),
});

const tagSchema = z.object({
  term: z.string(),
  AAT_URL: z.string(),
  Wikidata_URL: z.string(),
}).partial();

/**
 * https://metmuseum.github.io/#object
 */
export const ObjectResponseSchema = z.object({
  objectID: z.number().describe('Identifying number for each artwork (unique, can be used as key field)'),
  isHighlight: z.boolean().describe('When "true" indicates a popular and important artwork in the collection'),
  accessionNumber: z.string().describe('Identifying number for each artwork (not always unique)'),
  accessionYear: z.string().describe('Year the artwork was acquired'),
  isPublicDomain: z.boolean().describe('When "true" indicates the image is in the public domain'),
  primaryImage: z.string().describe('URL to the primary image of an object in JPEG format'),
  primaryImageSmall: z.string().describe('URL to the lower-res primary image of an object in JPEG format'),
  additionalImages: z.array(z.string()).describe('An array containing URLs to the additional images of an object in JPEG format'),
  constituents: z.array(constituentSchema).nullable().describe(
    'An array containing the constituents associated with an object, with the constituent\'s role, name, '
    + 'ULAN URL, Wikidata URL, and gender, when available (currently contains female designations only)',
  ),
  department: z.string().describe('Indicates The Met\'s curatorial department responsible for the artwork'),
  objectName: z.string().describe('Describes the physical type of the object'),
  title: z.string().describe('Title, identifying phrase, or name given to a work of art'),
  culture: z.string().describe('Information about the culture, or people from which an object was created'),
  period: z.string().describe('Time or time period when an object was created'),
  dynasty: z.string().describe('Dynasty (a succession of rulers of the same line or family) under which an object was created'),
  reign: z.string().describe('Reign of a monarch or ruler under which an object was created'),
  portfolio: z.string().describe('A set of works created as a group or published as a series'),
  artistRole: z.string().describe('Role of the artist related to the type of artwork or object that was created'),
  artistPrefix: z.string().describe('Describes the extent of creation or describes an attribution qualifier to the information given in the artistRole field'),
  artistDisplayName: z.string().describe('Artist name in the correct order for display'),
  artistDisplayBio: z.string().describe('Nationality and life dates of an artist, also includes birth and death city when known'),
  artistSuffix: z.string().describe('Used to record complex information that qualifies the role of a constituent'),
  artistAlphaSort: z.string().describe('Used to sort artist names alphabetically. Last Name, First Name, Middle Name, Suffix, and Honorific fields'),
  artistNationality: z.string().describe('National, geopolitical, cultural, or ethnic origins or affiliation of the creator'),
  artistBeginDate: z.string().describe('Year the artist was born'),
  artistEndDate: z.string().describe('Year the artist died'),
  artistGender: z.string().describe('Gender of the artist (currently contains female designations only)'),
  artistWikidata_URL: z.string().describe('Wikidata URL for the artist'),
  artistULAN_URL: z.string().describe('ULAN URL for the artist'),
  objectDate: z.string().describe('Year, a span of years, or a phrase that describes the specific or approximate date when an artwork was designed or created'),
  objectBeginDate: z.number().describe('Machine readable date indicating the year the artwork was started to be created'),
  objectEndDate: z.number().describe('Machine readable date indicating the year the artwork was completed'),
  medium: z.string().describe('Refers to the materials that were used to create the artwork'),
  dimensions: z.string().describe('Size of the artwork or object'),
  measurements: z.array(z.object({
    elementName: z.string(),
    elementDescription: z.string().nullable().optional(),
    elementMeasurements: z.record(z.string(), z.number()),
  })).nullable().describe('Array of elements, each with a name, description, and set of measurements. Spatial measurements are in centimeters; weights are in kg'),
  creditLine: z.string().describe('Text acknowledging the source or origin of the artwork and the year the object was acquired'),
  geographyType: z.string().describe('Type of location related to the artwork (e.g., "Made in", "From")'),
  city: z.string().describe('City associated with the artwork\'s creation'),
  state: z.string().describe('State or province associated with the artwork\'s creation'),
  county: z.string().describe('County associated with the artwork\'s creation'),
  country: z.string().describe('Country associated with the artwork\'s creation'),
  region: z.string().describe('Region associated with the artwork\'s creation'),
  subregion: z.string().describe('Subregion associated with the artwork\'s creation'),
  locale: z.string().describe('Locale associated with the artwork\'s creation'),
  locus: z.string().describe('Locus associated with the artwork\'s creation'),
  excavation: z.string().describe('Excavation associated with the artwork'),
  river: z.string().describe('River associated with the artwork\'s creation'),
  classification: z.string().describe('General term describing the artwork type'),
  rightsAndReproduction: z.string().describe('Credit line for artworks still under copyright'),
  linkResource: z.string().describe('URL to the object\'s page on metmuseum.org'),
  metadataDate: z.string().describe('Date metadata was last updated'),
  repository: z.string().describe('Indicates the repository containing the artwork'),
  objectURL: z.string().describe('URL to the object\'s page on metmuseum.org'),
  tags: z.array(tagSchema).nullable().describe('An array of subject keyword tags associated with the object'),
  objectWikidata_URL: z.string().describe('Wikidata URL for the object'),
  isTimelineWork: z.boolean().describe('Whether the artwork is featured on the Timeline of Art History website'),
  GalleryNumber: z.string().describe('Gallery number where artwork is located'),
}).partial(); // All fields are optional as the API may not return all fields for all objects
