from typing import Optional

import psycopg2.extras
from psycopg2.extras import RealDictCursor
from result import Result, Ok, Err

from models import Quiz, Question
from persistance.database import DBSession, Database


class QuizResults:
    def __init__(self, count: int, answered: int, correct: int):
        self.count = count
        self.answered = answered
        self.correct = correct


class QuizRepo:
    def __init__(self, database: Database):
        self.database = database

    def save(self, quiz: Quiz, user_id: Optional[str] = None) -> Quiz:
        """Creates a placeholder entry for a Quiz and returns the id"""
        quiz_id: str
        quiz_stmt = "INSERT INTO quizzes (owner_id, prompt) VALUES (%s, %s) RETURNING id;"
        question_stmt = "INSERT INTO questions (quiz_id, text) VALUES (%s, %s) RETURNING id;"
        options_stmt = "INSERT INTO options (question_id, text, correct) VALUES (%s, %s, %s);"

        with DBSession(self.database) as db:
            db.cursor.execute(quiz_stmt, (user_id, quiz.prompt))
            quiz_id = db.cursor.fetchone()[0]

            for question in quiz.questions:
                db.cursor.execute(question_stmt, (quiz_id, question.text))
                question_id = db.cursor.fetchone()[0]

                for i, option in enumerate(question.options):
                    is_correct = question.correct_answer_index == i
                    db.cursor.execute(options_stmt, (question_id, option, is_correct))

            db.conn.commit()

        quiz = self.get(quiz_id, user_id)
        return quiz

    def get(self, quiz_id: str, user_id: str) -> Quiz | None:
        stmt = """
        SELECT
        	q.id,
        	q.prompt quiz_prompt,
        	qu.id question_id,
        	qu.text question_text,
        	o.id option_id,
        	o.text option_text,
        	o.correct option_correct,
        	a.correct question_answered_correct
        FROM quizzes q
        JOIN questions qu ON q.id = qu.quiz_id
        JOIN options o ON qu.id = o.question_id
        LEFT JOIN user_quiz_answers a ON o.question_id = a.question_id
        WHERE q.id = %s AND q.owner_id = %s
        ORDER BY q.id, qu.id;"""

        results = []
        with DBSession(self.database, cursor_factory=RealDictCursor) as db:
            db.cursor.execute(stmt, (quiz_id, user_id))
            results = db.cursor.fetchall()

        if not results:
            return None

        quiz_prompt = ""
        rows_by_question_id = dict()
        for row in results:
            if not quiz_prompt:
                quiz_prompt = row["quiz_prompt"]

            if row["question_id"] not in rows_by_question_id:
                rows_by_question_id[row["question_id"]] = []

            rows_by_question_id[row["question_id"]].append(row)

        questions: list[Question] = []
        for question_id, option_rows in rows_by_question_id.items():
            options = [
                dict(text=x["option_text"], correct=x["option_correct"]) for x in option_rows
            ]

            correct_answer_index = 0
            for i, option in enumerate(options):
                if option["correct"]:
                    correct_answer_index = i
                    break

            q = Question(
                id=question_id,
                text=option_rows[0]["question_text"],
                options=[option["text"] for option in options],
                correct_answer=options[correct_answer_index]["text"],
                correct_answer_index=correct_answer_index,
                answered_correct=rows_by_question_id[question_id][0]["question_answered_correct"],
            )

            questions.append(q)

        return Quiz(id=quiz_id, prompt=quiz_prompt, questions=questions)

    def answer(self, quiz_id: str, question_id: int, option_index: int, user_id: str) -> bool:
        option_stmt = "SELECT correct FROM options WHERE question_id = %s ORDER BY id;"
        
        persist_answer_stmt = """
        INSERT INTO user_quiz_answers (user_id, quiz_id, question_id, correct)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, quiz_id, question_id)
            DO UPDATE SET correct = %s;"""
        
        with DBSession(self.database) as db:
            # Determine if the correct answer was selected
            db.cursor.execute(option_stmt, (question_id,))
            options = [x[0] for x in db.cursor.fetchall()]
            correct_index = options.index(True)
            
            # Persist if the answer was correct or not
            is_correct = option_index == correct_index
            db.cursor.execute(persist_answer_stmt, (user_id, quiz_id, question_id, is_correct, is_correct))
            db.conn.commit()

            return is_correct

    def get_results(self, quiz_id: str, user_id: str) -> QuizResults:
        stmt = """
        SELECT
            COUNT(q.id) AS count,
            COUNT(a.correct) AS answered,
            COALESCE(SUM(CASE WHEN a.correct THEN 1 ELSE 0 END), 0) AS correct
        FROM quizzes q
        JOIN questions qu ON q.id = qu.quiz_id
        LEFT JOIN user_quiz_answers a ON qu.id = a.question_id
        WHERE q.id = %s AND a.user_id = %s;"""

        with DBSession(self.database) as db:
            db.cursor.execute(stmt, (quiz_id, user_id))
            counts = db.cursor.fetchone()
            return QuizResults(count=counts[0], answered=counts[1], correct=counts[2])

    def get_current_question_id(self, quiz_id: str, user_id: str) -> Result[int, str]:
        stmt = """
        SELECT qu.id question_id
        FROM quizzes q
        JOIN questions qu ON q.id = qu.quiz_id
        LEFT JOIN user_quiz_answers a ON qu.id = a.question_id
        WHERE
            q.id = %s
            AND a.correct IS NULL
            AND a.user_id = %s
        ORDER BY qu.id
        LIMIT 1;"""

        first_question_stmt = "SELECT qu.id question_id FROM questions qu WHERE qu.quiz_id = %s ORDER BY qu.id LIMIT 1;"

        with DBSession(self.database, cursor_factory=RealDictCursor) as db:
            db.cursor.execute(stmt, (quiz_id, user_id))
            result = db.cursor.fetchone()

            if not result:
                # The user has finished the quiz or there are no questions or there is no quiz
                db.cursor.execute(first_question_stmt, (quiz_id,))
                question_result = db.cursor.fetchone()
                if not question_result:
                    return Err("The quiz does not exist")

                # Return the first question if the user has never answered a question in the quiz
                return Ok(question_result["question_id"])

            return Ok(result["question_id"])

            # return Question(
            #     id=result["question_id"],
            #     text=result["question_text"],
            #     options=[],
            #     correct_answer="",
            #     correct_answer_index=-1,
            # )


if __name__ == "__main__":
    q1 = Question(
        text="What is 1 + 1",
        options=["1", "2", "3", "4"],
        correct_answer="2",
        correct_answer_index=1,
    )
    q2 = Question(
        text="What is 2 + 2",
        options=["1", "2", "3", "4"],
        correct_answer="4",
        correct_answer_index=3,
    )
    test_quiz = Quiz(prompt="Can you do basic maths?", questions=[q1, q2])

    __db = Database.default(create_tables=True)
    repo = QuizRepo(__db)
    identifier = repo.save(test_quiz, None)
    print(identifier, type(identifier))
