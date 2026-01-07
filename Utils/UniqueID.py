from string import ascii_lowercase, digits, punctuation
from random import sample, shuffle

used_string = ascii_lowercase + digits + punctuation + '№,.-=+;%:?!абвгдеёжзийклмнопрстуфхцчшщъыьэюяії'


def string_to_ID(string):
    string = string.lower()
    global used_string
    result = ''
    for s in string:
        if s in used_string:
            result = result + str(used_string.index(s))
    result = sample(result, 10)
    shuffle(result)

    return "".join(result)


