def _normalize_value(value):
    if not isinstance(value, str):
        return value
    return value.strip().lower()


def _map_letter_answer(correct, options):
    if not isinstance(correct, str):
        return correct
    correct_text = correct.strip()
    if len(correct_text) == 1 and correct_text.upper() in 'ABCD' and len(options) == 4:
        idx = ord(correct_text.upper()) - 65
        if 0 <= idx < len(options):
            return options[idx]
    return correct


def evaluate(mcqs, user_answers):
    score = 0
    results = []

    for i, q in enumerate(mcqs):
        correct = _map_letter_answer(q['answer'], q['options'])
        user_ans = user_answers[i] if i < len(user_answers) else ""

        is_correct = _normalize_value(user_ans) == _normalize_value(correct)

        if is_correct:
            score += 1

        results.append({
            'question': q['question'],
            'correct': correct,
            'your_answer': user_ans,
            'status': '✅' if is_correct else '❌'
        })

    return score, results
