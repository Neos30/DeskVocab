from openai import OpenAI
import json
from pydantic import BaseModel
from typing import List, Optional

class WordSchema(BaseModel):
    word: str
    phonetic: str
    definition: str
    example_en: str
    example_cn: str

class AIGenerator:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)
        self.model = model

    def generate_words(self, scene: str, count: int = 5) -> List[WordSchema]:
        prompt = f"""
        You are a professional English teacher. Please generate {count} English words or phrases related to the scene: "{scene}".
        For each word, provide:
        1. The word itself.
        2. IPA phonetic transcription.
        3. Concise Chinese definition.
        4. An English example sentence.
        5. The Chinese translation of the example sentence.

        Return ONLY a JSON list of objects with keys: "word", "phonetic", "definition", "example_en", "example_cn".
        Do not include any other text or markdown formatting.
        """
        
        try:
            create_kwargs = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            }
            if "gpt-4-turbo" in self.model or "gpt-3.5-turbo" in self.model:
                create_kwargs["response_format"] = {"type": "json_object"}
            response = self.client.chat.completions.create(**create_kwargs)

            content = response.choices[0].message.content
            # Cleanup if the model ignored "only json" instruction
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            # Some models might return {"words": [...]} instead of a direct list
            if isinstance(data, dict) and "words" in data:
                data = data["words"]
            elif isinstance(data, dict) and not isinstance(data, list):
                # If it returned a single object, wrap it or find the list
                for val in data.values():
                    if isinstance(val, list):
                        data = val
                        break
            
            return [WordSchema(**item) for item in data]
        except Exception as e:
            print(f"Error generating words: {e}")
            return []
