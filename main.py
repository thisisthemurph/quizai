import os
from dotenv import load_dotenv
from quiz_builder import QuizBuilder


def main(openapi_api_key: str):
    topic = input("What would you like to have a quiz on?\n")
    num_questions = int(input("How many questions would you like?\n"))

    builder = QuizBuilder(api_key=openapi_api_key)
    quiz = builder.make_quiz(topic, num_questions)

    correct_answers = 0
    print(f"\n{quiz.prompt}\n")
    for i, question in enumerate(quiz.questions, start=1):
        print(f"{i}: {question.text}")
        for j, option in enumerate(question.options, start=1):
            print(f"\t{j}) {option}")

        answer = int(input("\nAnswer: ")) - 1
        if answer == question.correct_answer_index:
            correct_answers += 1
            print("👏 correct!\n")
        else:
            print(f"Incorrect. The correct answer was: {question.correct_answer}\n")

    if correct_answers < len(quiz) / 2:
        prefix = "Too bad."
    else:
        prefix = "Well done!"

    print(f"{prefix} You scored {correct_answers} out of {len(quiz)}")


if __name__ == "__main__":
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")

    main(openai_api_key)
