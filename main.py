from pathlib import Path


def parse_questions(file_path):
    """
    Читает один файл с вопросами и парсит его в словарь.
    
    :param file_path: Путь к текстовому файлу.
    :return: Словарь вида {текст_вопроса: текст_ответа}.
    """
    questions = {}
    
    with open(file_path, encoding='koi8-r') as file:
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


def load_all_questions():
    """Собирает вопросы из всех txt-файлов в папке questions в один большой словарь."""
    questions_dir = Path('questions')
    all_questions = {}
    
    if not questions_dir.exists():
        print(f"Ошибка: папка '{questions_dir}' не найдена.")
        return all_questions

    for file_path in questions_dir.glob('*.txt'):
        # Парсим файл и получаем словарь
        file_questions = parse_questions(file_path)
        # Метод update добавляет ключи и значения из одного словаря в другой
        all_questions.update(file_questions)
        
    return all_questions


if __name__ == '__main__':
    questions = load_all_questions()
    
    print(f"Всего загружено вопросов: {len(questions)}\n")
    
    # Выводим первые 3 вопроса для проверки, что парсинг работает
    for i, (question, answer) in enumerate(questions.items()):
        if i >= 3:
            break
        print(f"Вопрос: {question}")
        print(f"Ответ: {answer}\n")