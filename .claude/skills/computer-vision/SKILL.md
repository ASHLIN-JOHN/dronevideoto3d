# Computer Vision Integration

## Purpose
Use AI vision models to analyze drone video frames and extract structured scene data.

## API: Groq Vision
- Model: qwen/qwen3.6-27b
- Endpoint: https://api.groq.com/openai/v1/chat/completions
- Auth: Bearer token from GROQ_API_KEY in .env
- Input: base64 JPEG frames (max 512x512)

## Prompt Structure
System prompt instructs model to return JSON with:
- objects[]: type, position, color, estimated_size, confidence
- terrain: type, color, features
- road: present, direction, type
- weather/lighting conditions

## Response Handling
1. Try parsing response_format: json_object
2. On 400 error, retry without response_format
3. Extract JSON from raw text using regex: r'\{[\s\S]*\}'
4. Validate required fields exist
5. Skip frame on 3 consecutive failures

## Rate Limit Strategy
- Sleep 3s between frames
- On 429: wait 30s, retry
- Max 3 retries per frame
- Emit progress signals per frame

## Security
- API key in .env only, never logged/printed/committed
- Frames processed in memory, not saved to disk
- No external URLs generated from responses
