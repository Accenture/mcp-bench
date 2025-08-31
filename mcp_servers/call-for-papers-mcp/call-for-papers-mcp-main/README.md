# Call For Papers MCP

A Smithery MCP for searching academic conferences and events from WikiCFP.

## Description

ConferenceSearcher allows you to search for upcoming academic conferences and events based on keywords. It scrapes conference information from WikiCFP and returns detailed information about each matching event, including name, description, dates, location, and submission deadlines.

## Tool: getEvents

Search for conferences matching specific keywords.

### Parameters

- `keywords` (string, required): Keywords to search for conferences (e.g., 'ai agent', 'machine learning')
- `limit` (number, optional): Maximum number of events to return (default: 10)

### Returns

A JSON object with the following properties:

- `status`: Status of the operation (success/error)
- `count`: Number of events found
- `events`: Array of conference events, each containing:
  - `event_name`: Name of the conference
  - `event_description`: Description of the conference
  - `event_time`: Date and time of the conference
  - `event_location`: Location of the conference
  - `deadline`: Submission deadline
  - `event_link`: Link to the conference page on WikiCFP

## License

MIT