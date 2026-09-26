```python
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from schemas import ExtractedIncident


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY was not found. Check your .env file."
    )


client = genai.Client(api_key=api_key)


def extract_incident_data(description: str) -> ExtractedIncident:

    prompt = f"""
You are an information extraction system for a disaster-response
prototype called CrisisGrid.

Extract structured emergency information from the report below.

Rules:

- Extract only information supported by the report.
- Do not invent facts.

- disaster_type should be a short label such as:
  flood, earthquake, fire, cyclone, medical,
  road_blockage, relief_request, or other.

- people_affected must be at least 1.
  If the exact number is unknown, use the minimum number
  clearly supported by the report.

- vulnerable_people means clearly mentioned elderly people,
  children, people with disabilities, or other vulnerable people.

- injuries means people explicitly described as injured.

- mobility_issue should be true only if someone has difficulty
  moving or evacuating.

- required_resources should contain the resources that would
  reasonably be needed to respond to the situation.

- These resources do not need to be explicitly requested by
  the person reporting the emergency.

- Infer them carefully from the situation.

Examples:
  rising flood water + trapped people -> rescue_team, boat
  injured person -> ambulance, medical_team
  medicine shortage -> medicine
  shelter without drinking water -> water

- Do not add resources that are unrelated to the report.

- Put uncertain information into uncertainty_notes.

- Do NOT calculate priority.
- Do NOT calculate danger level.

Emergency report:

{description}
"""

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractedIncident,
                ),
            )

            if not response.text:
                raise ValueError(
                    "Gemini returned an empty response."
                )

            return ExtractedIncident.model_validate_json(
                response.text
            )

        except Exception as e:

            error_message = str(e)

            # Retry temporary Gemini/API availability errors
            if any(
                code in error_message
                for code in ["429", "500", "502", "503", "504"]
            ):
                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    time.sleep(delay)
                    continue

            # Re-raise all non-retryable errors
            raise
```
