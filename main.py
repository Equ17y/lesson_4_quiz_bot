import os
import argparse
from pathlib import Path


def parse_questions(file_path):
    """
    Читает один файл с вопросами и парсит его в словарь.
    """
    questions = {}
    with open(file_path, encoding='utf-8') as file:
        content = file.read()
    
    blocks = content.split('\n\n')
    current_question = None
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith('Вопрос'):
            lines = block.split('\n')
            if len(lines) > 1:
                current_question = '\n'.join(lines[1:]).strip()
        elif block.startswith('Ответ') and current_question is not None:
            lines = block.split('\n')
            if len(lines) > 1:
                answer = '\n'.join(lines[1:]).strip()
                questions[current_question] = answer
                current_question = None
    return questions


def load_all_questions(questions_dir=None):
    """
    Собирает вопросы из всех txt-файлов в указанной папке в один словарь.
    """
    if questions_dir is None:
        questions_dir = os.getenv('QUESTIONS_DIR', 'questions')
    
    all_questions = {}
    questions_path = Path(questions_dir)
    
    if not questions_path.exists():
        return all_questions
    
    for file_path in questions_path.glob('*.txt'):
        file_questions = parse_questions(file_path)
        all_questions.update(file_questions)
    
    return all_questions


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Парсер вопросов для бота-викторины'
    )
    parser.add_argument(
        '--questions-dir',
        type=str,
        default='questions',
        help='Путь к папке с вопросами (по умолчанию: questions)'
    )
    args = parser.parse_args()
    
    questions = load_all_questions(args.questions_dir)
    print(f"Всего загружено вопросов: {len(questions)}\n")
    
    for i, (question, answer) in enumerate(questions.items()):
        if i >= 3:
            break
        print(f"Вопрос: {question}")
        print(f"Ответ: {answer}\n")