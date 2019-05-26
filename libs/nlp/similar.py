"""
@Author Felix Hedenström
"""

import random
import time
import numpy as np

class PossibilitiesFinder:
    
    def __init__(self, w1, candidates, distance_limit):
        
        
        self._max_word_length = 100
        self._word = w1.lower()
        self._lastword = ""
        
        self._distance_limit = distance_limit
        
        self._d = np.zeros((self._max_word_length, self._max_word_length))
        
        for i in range(0, self._max_word_length):
            self._d[i][0] = i
        
        for j in range(0, self._max_word_length):
            self._d[0][j] = j
        
        self._closest_distance = self._max_word_length + 1
        self._word_size = len(self._word)
        self._candidates = candidates
        
    def shared_letters(w1, w2):
        length = min(len(w1), len(w2))
        c = 0
        for i in range(0, length):
            if w1[i] == w2[i]:
                c += 1
            else:
                return c
        return c
        
    def run(self):
        answer = []
        for c in self._candidates:
            if abs(len(c) - self._word_size) > self._closest_distance:
                continue
                
            dist = self._editdistance(c.lower())
            if self._closest_distance <= self._distance_limit and dist <= self._distance_limit:
                answer.append(c)
            else:     
                if dist < self._closest_distance:
                    self._closest_distance = dist
                    answer = [c]
                elif dist == self._closest_distance:
                    answer.append(c)
        return answer
    # Finds the editdistance between self._word and w2
    def _editdistance(self, w2):
        
        n = len(w2)
        
        shared_letters = PossibilitiesFinder.shared_letters(self._lastword, w2)
        
        for j in range(shared_letters + 1, n + 1):
            for i in range(1, self._word_size + 1):
                if self._word[i - 1] == w2[j - 1]:
                    self._d[i][j] = self._d[i - 1][j - 1]
                else:
                    self._d[i][j] = min(
                                            self._d[i - 1][j    ],
                                            self._d[i    ][j - 1],
                                            self._d[i - 1][j - 1]
                                       ) + 1
        self._lastword = w2
        return self._d[self._word_size][n]

def levenshtein(word1, word2):
    assert type(word1) == str, "Arguments must be strings"
    assert type(word2) == str, "Arguments must be strings" 

    return _levenshtein(word1.lower(),word2.lower(), len(word1),len(word2))
    
def possibilities(word, candidates, alternatives=10, subsets=False, use_random=False, alllowerthan=0):
    """
    alternatives = 0
    means that all results will be returned.
    
    All lower than means that, if available, all words with editdistance lower or equal to <alllowerthan>
    will be returned. If no words are found with editdistance lower than <alllowerthan>, the lowest found will 
    be returned.
    
    Example:
    alllowerthan = 4, alternatives = 0
    returns all options where editdistance is 4 or lower if any exists.
    """
    assert type(word) == str, "The word must be in the form of a string, was a {}.".format(type(word))
    assert type(candidates) == list, "The candidates must be a list, was a {}".format(type(candidates))
    assert len(candidates) > 0, "Candidates must contain atleast one element."
    assert type(candidates[0]), "The list of candidates can only contain strings."
    word = word.lower()
    lword = len(word)
    inword = []
    wordin = []
    
    if subsets:
        for w in candidates:
            wlower = w.lower()
            if word in wlower:
                wordin.append(w)
            elif wlower in word:
                inword.append(w)

    finder = PossibilitiesFinder(word, candidates, alllowerthan)
    shortest = finder.run()
    
    if use_random:
        random.shuffle(shortest)
    ans =  list(set(inword + wordin + shortest))   
    if alternatives == 0:
        return ans
    else:
        return ans[:alternatives - 1]
    
    
def editdistance(word1, word2):
    return levenshtein(word1, word2)

def _levenshtein(s, t, m, n):
    d = np.zeros((m + 1, n + 1))
    for i in range(1, m + 1):
        d[i][0] = i
    for j in range(1, n + 1):
        d[0, j] = j
    for j in range(1, n + 1):
        for i in range(1, m + 1):
            if s[i - 1] == t[j - 1]:
                subcost = 0
            else:
                subcost = 1
            d[i][j] = min(  d[i - 1][j    ] + 1, #Delete
                            d[i    ][j - 1] + 1, #Insert
                            d[i - 1][j - 1] + subcost # Sub
                         )
    
    return d[m,n]
    
