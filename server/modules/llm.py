import os
from groq import Groq

class GroqLLM:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = Groq(api_key=api_key)
        self.model='openai/gpt-oss-20b'
        prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts')
        self.full_prompt=open(os.path.join(prompts_dir, 'full-report-generator.txt'), 'r').read()
        self.partial_prompt=open(os.path.join(prompts_dir, 'partial-report-generator.txt'), 'r').read()


    def llm(self, content, prev_content=None, is_full=False):
        user_content = 'Transcription:\n\n' + content if is_full else 'Transcription:\n\n' + content + '\n\nPrevious Transcription:\n\n' + prev_content

        stream = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": self.full_prompt if is_full else self.partial_prompt,
                },
                {
                    "role": "user",
                    "content": user_content,
                }
            ],
            model=self.model,
            temperature=0.1,
            top_p=1,
            max_completion_tokens=1024,
            stop=None,
            stream=True,
        )

        for chunk in stream:
            yield chunk.choices[0].delta.content
