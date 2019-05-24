"""
@Author Felix Hedenström
"""

import random

def first_vowel_index(word):
    """
    Returns the index of the first vowel.
    If no vowel exists, return length of word.
    """
    vowels = 'aeiouyåäö'
    index = None
    for i in range(len(word)):
        if word[i] in vowels:
            return i

def spoon(text):

    """
    1. Strips spaces from the beginning and end of the input, removes control charaters (linefeed etc), and makes everything lower-case.

    2. Separates the input into words (by breaking it up wherever a space is found)

    3. Any words which begin with a vowel or are only one letter long are left alone.

    4. Any words longer than one letter and begin with a consonant go through the following process:

    i) Any letters before the first vowel are extracted
    ii) The 'starts' of these words are shuffled around
    iii) The words are re-assembled with the starts shuffled

    5. The sentence is re-formed (like a fish finger) with all the words in (3) left as they were, and all the others put back with the starts shuffled around.

    6. The first character is capitalised, as is so often neglected on the net nowadays... (!)
    """

    #1.
    text = text.strip().lower()
    #2.
    words = text.split(" ")
    tmp = []
    starts = list()
    for word in words:
        index = first_vowel_index(word)
        # 3
        if len(word) == 1 or index == 0:
            tmp.append(("",word))
        else:
            tmp.append((word[:index], word[index:]))
            starts.append(word[:index])
    res = list()
    oldstarts = list(starts)

    random.shuffle(starts)

    if oldstarts == starts:
        starts = list(reversed(starts))

    for start, end in tmp:
        if start == "":
            res.append(end)
        else:
            res.append("{}{}".format(starts.pop(0), end))
    ans = res[0]
    ans += " {}".format(" ".join(res[1:]))
    return ans
