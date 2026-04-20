import re


def _clean_option_text(option):
    if not isinstance(option, str):
        return option
    cleaned = option.strip()
    # Normalize options like "A. foo", "B) bar", "C - baz" to plain text.
    cleaned = re.sub(r'^[A-Da-d]\s*[\.|\)|:|-]\s*', '', cleaned)
    return cleaned.strip()


def _normalize_answer(answer, options):
    if not isinstance(answer, str) or not answer.strip():
        return answer

    answer_text = answer.strip()
    normalized_options = [opt.strip() for opt in options]

    if len(answer_text) == 1 and answer_text.upper() in 'ABCD' and len(normalized_options) == 4:
        return normalized_options[ord(answer_text.upper()) - 65]

    if len(answer_text) > 1 and answer_text[0].upper() in 'ABCD' and answer_text[1] in '.) :-':
        stripped = answer_text[2:].strip()
        for opt in normalized_options:
            if stripped.lower() == opt.lower():
                return opt

    for opt in normalized_options:
        if answer_text.lower() == opt.lower():
            return opt

    return answer_text


def validate_mcqs(mcqs):
    valid = []

    for q in mcqs:
        if (
            'question' in q and
            'options' in q and
            isinstance(q['options'], list) and
            len(q['options']) == 4 and
            'answer' in q
        ):
            q['options'] = [_clean_option_text(opt) for opt in q['options']]
            q['answer'] = _normalize_answer(q['answer'], q['options'])
            valid.append(q)

    return valid
