import psycopg2.extras

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

    def create(self, quiz: Quiz) -> Quiz:
        """Creates a placeholder entry for a Quiz and returns the id"""
        quiz_id: str
        quiz_stmt = "INSERT INTO quizzes (prompt) VALUES (%s) RETURNING id;"
        question_stmt = "INSERT INTO questions (quiz_id, text) VALUES (%s, %s) RETURNING id;"
        options_stmt = "INSERT INTO options (question_id, text, correct) VALUES (%s, %s, %s);"

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

        quiz = self.get(quiz_id)
        return quiz

    def get(self, quiz_id: str) -> Quiz | None:
        stmt = """SELECT 
                q.prompt quiz_prompt,
                qu.id question_id,
                qu.text question_text,
                qu.answered_correct question_answered_correct,
                o.id option_id,
                o.text option_text,
                o.correct option_correct
            FROM quizzes q
            JOIN questions qu on q.id = qu.quiz_id
            JOIN options o ON qu.id = o.question_id
            WHERE q.id = %s
            ORDER BY q.id, qu.id;"""

        results = []
        with DBSession(self.database, cursor_factory=psycopg2.extras.RealDictCursor) as db:
            db.cursor.execute(stmt, (quiz_id,))
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
            options = [dict(text=x["option_text"], correct=x["option_correct"]) for x in option_rows]

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

    def answer(self, quiz_id: str, question_id: int, option_index: int) -> Quiz:
        option_stmt = "SELECT correct FROM options WHERE question_id = %s ORDER BY id;"
        update_stmt = "UPDATE questions SET answered_correct = %s WHERE quiz_id = %s AND id = %s;"

        quiz = self.get(quiz_id)
        with DBSession(self.database) as db:
            # Determine if the correct answer was selected
            db.cursor.execute(option_stmt, (question_id, ))
            options = [x[0] for x in db.cursor.fetchall()]
            correct_index = options.index(True)

            # Persist if the answer was correct or not
            db.cursor.execute(update_stmt, (option_index == correct_index, quiz_id, question_id))
            db.conn.commit()

        return quiz

    def get_results(self, quiz_id) -> QuizResults:
        stmt = """SELECT
                    COUNT(q.id) AS count,
                    SUM(CASE WHEN qu.answered_correct IS NOT NULL THEN 1 ELSE 0 END) AS answered,
                    SUM(CASE WHEN qu.answered_correct THEN 1 ELSE 0 END) AS correct
                  FROM quizzes q
                  JOIN questions qu ON q.id = qu.quiz_id
                  WHERE q.id = %s;"""

        with DBSession(self.database) as db:
            db.cursor.execute(stmt, (quiz_id,))
            counts = db.cursor.fetchone()
            # return dict(question_count=counts[0], correct_count=counts[1])
            return QuizResults(count=counts[0], answered=counts[1], correct=counts[2])

    def get_current_question(self, quiz_id: str) -> Question | None:
        stmt = """SELECT
        	q.id AS quiz_id,
        	qu.id AS question_id,
        	qu.text
        FROM quizzes q
        JOIN questions qu ON q.id = qu.quiz_id
        WHERE q.id = %s
        	AND qu.answered_correct IS NULL
        ORDER BY qu.id
        LIMIT 1;"""

        with DBSession(self.database) as db:
            db.cursor.execute(stmt, (quiz_id,))
            result = db.cursor.fetchone()
            if not result:
                return None
            return Question(id=result[1], text=result[2], options=[], correct_answer='', correct_answer_index=-1)


if __name__ == "__main__":
    q1 = Question(text="What is 1 + 1", options=["1", "2", "3", "4"], correct_answer="2", correct_answer_index=1)
    q2 = Question(text="What is 2 + 2", options=["1", "2", "3", "4"], correct_answer="4", correct_answer_index=3)
    test_quiz = Quiz(prompt="Can you do basic maths?", questions=[q1, q2])

    __db = Database.default(create_tables=True)
    repo = QuizRepo(__db)
    identifier = repo.create(test_quiz)
    print(identifier, type(identifier))
