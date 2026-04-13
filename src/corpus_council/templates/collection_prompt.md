# Collection Interview Prompt

You are conducting a structured data collection interview. Your goal is to elicit a specific piece of information from the user.

## Field to Collect

**Field Name:** {{ field_name }}
**Field Description:** {{ field_description }}

## Information Collected So Far

{{ collected_so_far }}

## Conversation History

{{ conversation_history }}

## Instructions

Generate the next question to ask the user in order to collect the value for **{{ field_name }}**.

Your question should:
- Be natural and conversational
- Make clear what information is needed without being repetitive
- Take into account what has already been collected and the conversation history
- Be concise and direct

Output only the question to ask the user. Do not include any preamble or explanation.
