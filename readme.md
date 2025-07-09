# HubSpot + Vanna Flask API

This Flask app connects to Vanna agents and returns combined usage and HubSpot data.

## Endpoints

### `POST /query`

**Payload:**
```json
{
  "flow": "1",  // or "2"
  "query": "show me users who signed up last week"
}
