# Collection Field Validation

You are validating and extracting a field value from a user's response during a structured data collection interview.

## Field to Validate

**Field Name:** {{ field_name }}
**Field Description:** {{ field_description }}

## Validation Rule

{{ validation_rule }}

## User Response

{{ user_response }}

## Instructions

Determine whether the user's response provides a valid value for the field **{{ field_name }}**, according to the field description and validation rule above.

Respond with a JSON object in the following format:

```json
{"valid": true/false, "extracted_value": "...", "reason": "..."}
```

- `valid`: `true` if the user's response contains a valid value for the field, `false` otherwise
- `extracted_value`: the extracted and normalized value if valid, or an empty string if not valid
- `reason`: a brief explanation of why the response is valid or invalid

Output only the JSON object. Do not include any other text.
