from pydantic import BaseModel


class Question(BaseModel):
    id: int | None = None
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
    id: str | None = None
    prompt: str
    questions: list[Question]

    def __len__(self):
        return len(self.questions)

    def __str__(self):
        return self.prompt

    def __repr__(self):
        return f"Quiz(prompt={self.prompt})"

    def get_question_index(self, question_id: int):
        """Returns the index of the given question id or -1 if the id does not exist.
        Raises a ValueError if the id of any question is None"""
        question_ids = [q.id for q in self.questions]
        if None in question_ids:
            raise ValueError("Some questions do not have an ID set and cannot be compared")

        return question_ids.index(question_id)
