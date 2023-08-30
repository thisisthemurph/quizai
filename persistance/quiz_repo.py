from models import Quiz, Question
from persistance.database import DBSession, Database


class QuizRepo:
    def __init__(self, database: Database):
        self.database = database

    def create(self, quiz: Quiz) -> str:
        """Creates a placeholder entry for a Quiz and returns the id"""
        quiz_id: str
        quiz_stmt = "INSERT INTO quizzes (prompt) VALUES (%s) RETURNING id"
        question_stmt = "INSERT INTO questions (quiz_id, text) VALUES (%s, %s) RETURNING id"
        options_stmt = "INSERT INTO options (question_id, text, correct) VALUES (%s, %s, %s)"

        with DBSession(self.database) as db:
            db.cursor.execute(quiz_stmt, (quiz.prompt,))
            quiz_id = db.cursor.fetchone()[0]

            for question in quiz.questions:
                db.cursor.execute(question_stmt, (quiz_id, question.text))
                question_id = db.cursor.fetchone()[0]

                for i, option in enumerate(question.options):
                    is_correct = question.correct_answer_index == i
                    db.cursor.execute(options_stmt, (question_id, option, is_correct))

            db.conn.commit()

        return quiz_id


if __name__ == "__main__":
    q1 = Question(text="What is 1 + 1", options=["1", "2", "3", "4"], correct_answer="2", correct_answer_index=1)
    q2 = Question(text="What is 2 + 2", options=["1", "2", "3", "4"], correct_answer="4", correct_answer_index=3)
    test_quiz = Quiz(prompt="Can you do basic maths?", questions=[q1, q2])

    db = Database.default()
    repo = QuizRepo(db)
    identifier = repo.create(test_quiz)
    print(identifier, type(identifier))
