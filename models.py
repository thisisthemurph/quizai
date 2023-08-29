from pydantic import BaseModel


class Question(BaseModel):
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


class Quiz(BaseModel):
    prompt: str
    questions: list[Question]

    def __len__(self):
        return len(self.questions)

    def __str__(self):
        return self.prompt

    def __repr__(self):
        return f"Quiz(prompt={self.prompt})"