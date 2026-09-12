```json
{
  "cachedContent": "string",
  "contents": [
    {
      "role": "string",
      "parts": [
        {
          // Union field data can be only one of the following:
          "text": "string",
          "inlineData": {
            "mimeType": "string",
            "data": "string"
          },
          "fileData": {
            "mimeType": "string",
            "fileUri": "string"
          },
          // End of list of possible types for union field data.

          "videoMetadata": {
            "startOffset": {
              "seconds": "integer",
              "nanos": "integer"
            },
            "endOffset": {
              "seconds": "integer",
              "nanos": "integer"
            }
          }
        }
      ]
    }
  ],
  "systemInstruction": {
    "role": "string",
    "parts": [
      {
        "text": "string"
      }
    ]
  },
  "tools": [
    {
      "functionDeclarations": [
        {
          "name": "string",
          "description": "string",
          "parameters": {
            "object" 
          }
        }
      ]
    }
  ],
  "safetySettings": [
    {
      "category": "enum",
      "(HarmCategory)",
      "threshold": "enum",
      "(HarmBlockThreshold)"
    }
  ],
  "generationConfig": {
    "temperature": "number",
    "topP": "number",
    "topK": "number",
    "candidateCount": "integer",
    "maxOutputTokens": "integer",
    "presencePenalty": "float",
    "frequencyPenalty": "float",
    "stopSequences": [
      "string"
    ],
    "responseMimeType": "string",
    "responseSchema": "schema",
    "seed": "integer",
    "responseLogprobs": "boolean",
    "logprobs": "integer",
    "audioTimestamp": "boolean"
  },
  "labels": {
    "string": "string"
  }
}
```