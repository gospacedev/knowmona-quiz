from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
  model="gpt-4o",
  messages=[
    {
      "role": "system",
      "content": [
        {
          "type": "text",
          "text": "Create 10 multiple-choice questions about rotational kinematics with these requirements:\n    - average difficulty level\n    - casual tone\n    - 4 choices per question\n    - JSON format with array structure\n    - Keys: Q#, choice_1 to choice_4, answer, explanation\n    - No repeated questions\n    - Valid JSON syntax with proper commas and quotes\n    - Wrap all questions in a JSON array\n    - Separate each question object with a comma\n\n    User inputs: None\n\n    Please only return JSON with correct syntax"
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "Starting"
        }
      ]
    }
  ],
  response_format={
    "type": "text"
  },
  temperature=1,
  max_completion_tokens=2048,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0
)