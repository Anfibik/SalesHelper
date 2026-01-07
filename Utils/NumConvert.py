def number_to_words(number):
    """
    Преобразует число в словесное представление валюты гривна с учетом склонений.

    Args:
    number (int): Число для преобразования в слова.

    Returns:
    str: Словесное представление числа с учетом склонений.
    """
    units = ['', 'одна', 'дві', 'три', 'чотири', 'п\'ять', 'шість', 'сім', 'вісім', 'дев\'ять']
    tens = ['', 'десять', 'двадцять', 'тридцять', 'сорок', 'п\'ятдесят', 'шістдесят', 'сімдесят', 'вісімдесят',
            'дев\'яносто']
    hundreds = ['', 'сто', 'двісті', 'триста', 'чотириста', 'п\'ятсот', 'шістсот', 'сімсот', 'вісімсот', 'дев\'ятсот']
    thousands = ['тисяча', 'тисячі', 'тисяч']
    millions = ['мільйон', 'мільйона', 'мільйонів']
    billions = ['мільярд', 'мільярда', 'мільярдів']

    result = ''
    if number < 0:
        result = 'мінус '
        number = abs(number)

    if number < 10:
        result += units[number]
    elif number < 20:
        result += tens[number - 10]
    elif number < 100:
        result += tens[number // 10] + ' ' + units[number % 10]
    elif number < 1000:
        result += hundreds[number // 100] + ' ' + number_to_words(number % 100)
    elif number < 1000000:
        result += number_to_words(number // 1000) + ' ' + thousands[get_index_of_number(number // 1000)]
        if number % 1000 > 0:
            result += ' ' + number_to_words(number % 1000)
    elif number < 1000000000:
        result += number_to_words(number // 1000000) + ' ' + millions[get_index_of_number(number // 1000000)]
        if number % 1000000 > 0:
            result += ' ' + number_to_words(number % 1000000)
    else:
        result += number_to_words(number // 1000000000) + ' ' + billions[get_index_of_number(number // 1000000000)]
        if number % 1000000000 > 0:
            result += ' ' + number_to_words(number % 1000000000)

    return result.strip()


def get_index_of_number(number):
    """
    Возвращает индекс для правильного склонения слов.

    Args:
    number (int): Число для определения склонения.

    Returns:
    int: Индекс для правильного склонения слов.
    """
    if number % 10 == 1 and number % 100 != 11:
        return 0
    elif 2 <= number % 10 <= 4 and not (12 <= number % 100 <= 14):
        return 1
    else:
        return 2


