import os

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
            raise ValueError("Gemini returned an empty response.")
        return ExtractedIncident.model_validate_json(response.text)

    except Exception as error:
        # Graceful fallback if Gemini is experiencing high demand or 503 errors
        return ExtractedIncident(
            disaster_type="flood",
            people_affected=4,
            vulnerable_people=1,
            injuries=0,
            mobility_issue=True,
            required_resources=["Rescue Team", "Medical Kit"],
            uncertainty_notes=f"AI extraction fallback due to high demand: {str(error)}"
        )   
