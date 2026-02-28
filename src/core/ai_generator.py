from openai import OpenAI
import json
import traceback
from pydantic import BaseModel
from typing import List
from src.utils.logger import get_logger

logger = get_logger()

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

    def test_connection(self) -> tuple[bool, str]:
        """发送最小请求验证 API 配置是否可用。返回 (ok, message)。"""
        logger.info(f"[连接验证] model={self.model}, base_url={self.client.base_url}")
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Reply with the single word: ok"}],
                max_tokens=10,
            )
            reply = resp.choices[0].message.content.strip()
            logger.info(f"[连接验证] 成功，模型回复: {reply!r}")
            return True, f"连接成功，模型回复: {reply}"
        except Exception as e:
            msg = str(e)
            logger.error(f"[连接验证] 失败: {msg}\n{traceback.format_exc()}")
            return False, msg

    def generate_words_from_doc(self, text: str, count: int = 10) -> List[WordSchema]:
        """
        根据文档原文，让 AI 提取高频且有学习价值的英文单词。
        自动排除常用停用词（代词、介词、连接词等）。
        """
        # 截取前 3000 字符避免超出 token 限制
        excerpt = text[:3000]
        prompt = f"""
        You are a professional English teacher analyzing a document excerpt.
        From the text below, identify the {count} most frequent and meaningful English words or phrases
        that are worth learning. Exclude common stop words such as pronouns, prepositions, conjunctions,
        and articles (e.g., the, a, in, of, and, I, you, it, is, are, was, were, etc.).

        For each selected word, provide:
        1. The word itself.
        2. IPA phonetic transcription.
        3. Concise Chinese definition.
        4. An English example sentence.
        5. The Chinese translation of the example sentence.

        Return ONLY a JSON list of objects with keys: "word", "phonetic", "definition", "example_en", "example_cn".
        Do not include any other text or markdown formatting.

        Document excerpt:
        \"\"\"
        {excerpt}
        \"\"\"
        """

        logger.info(f"[文档生成单词] 开始 | 文本长度={len(text)} count={count} model={self.model}")
        logger.debug(f"[文档生成单词] 截取前 3000 字符作为输入")

        try:
            create_kwargs = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            }
            if "gpt-4-turbo" in self.model or "gpt-3.5-turbo" in self.model:
                create_kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**create_kwargs)
            content = response.choices[0].message.content
            logger.debug(f"[文档生成单词] 原始响应:\n{content}")

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)

            if isinstance(data, dict) and "words" in data:
                data = data["words"]
            elif isinstance(data, dict):
                for val in data.values():
                    if isinstance(val, list):
                        data = val
                        break

            words = [WordSchema(**item) for item in data]
            logger.info(f"[文档生成单词] 成功，共 {len(words)} 个: {[w.word for w in words]}")
            return words

        except json.JSONDecodeError as e:
            logger.error(f"[文档生成单词] JSON 解析失败: {e}\n原始内容: {content!r}")
            return []
        except Exception as e:
            logger.error(f"[文档生成单词] 异常: {e}\n{traceback.format_exc()}")
            return []

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

        logger.info(f"[生成单词] 开始 | scene={scene!r} count={count} model={self.model}")
        logger.debug(f"[生成单词] Prompt:\n{prompt.strip()}")

        try:
            create_kwargs = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            }
            if "gpt-4-turbo" in self.model or "gpt-3.5-turbo" in self.model:
                create_kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**create_kwargs)
            content = response.choices[0].message.content
            logger.debug(f"[生成单词] 原始响应:\n{content}")

            # 处理 markdown 代码块
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)

            if isinstance(data, dict) and "words" in data:
                data = data["words"]
            elif isinstance(data, dict):
                for val in data.values():
                    if isinstance(val, list):
                        data = val
                        break

            words = [WordSchema(**item) for item in data]
            logger.info(f"[生成单词] 成功，共 {len(words)} 个: {[w.word for w in words]}")
            return words

        except json.JSONDecodeError as e:
            logger.error(f"[生成单词] JSON 解析失败: {e}\n原始内容: {content!r}")
            return []
        except Exception as e:
            logger.error(f"[生成单词] 异常: {e}\n{traceback.format_exc()}")
            return []
