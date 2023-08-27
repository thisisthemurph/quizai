import json

import openai
import pydantic



prompt = """You are a  quiz master. You will be provided with a topic followed by a | character and then the number of questions required. Produce a quiz consisting of the given number of questions, each with 4 possible answers. Only one of the answers should be correct. The response should be in JSON format. The response should only include the JSON.

The json should have the following format:

{
  "prompt": "the original quiz prompt",
  "questions": [
    {
      "text": "",
      "options": [
        "option1",
        "option2",
        "option3",
        "option4"
      ],
      "correct_answer": "option2",
      "correct_answer_index": 1
    }
  ]
}"""


class Question(pydantic.BaseModel):
    text: str
    options: list[str]
    correct_answer: str
    correct_answer_index: int

    def __len__(self):
        return len(self.options)

    def __str__(self):
        return self.text

    def __repr__(self):
        return f"Question(text={self.text})"


class Quiz(pydantic.BaseModel):
    prompt: str
    questions: list[Question]

    def __len__(self):
        return len(self.questions)

    def __str__(self):
        return self.prompt

    def __repr__(self):
        return f"Quiz(prompt={self.prompt})"


class QuizBuilder:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.messages = [{"role": "system", "content": prompt}]

    def make_quiz(self, topic: str, num_questions: int = 10) -> Quiz:
        self.messages.append({"role": "user", "content": f"{topic} | {num_questions}"})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=self.messages
        )

        quiz_json = response.choices[0].message.content
        quiz_dict = json.loads(quiz_json)
        return Quiz(**quiz_dict)
