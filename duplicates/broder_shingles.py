#!/usr/bin/env python

"""
This just a draft for homework 'near-duplicates'
Use MinshinglesCounter to make result closer to checker
"""

import sys
import re

from collections import Counter, OrderedDict
from itertools import combinations
from operator import itemgetter

import mmh3

from docreader import *


class MinshinglesCounter:
    SPLIT_RGX = re.compile(r'\w+', re.U)

    def __init__(self, window=5, n=20):
        self.window = window
        self.n = n

    def count(self, text):
        words = MinshinglesCounter._extract_words(text)
        shs = self._count_shingles(words)
        mshs = self._select_minshingles(shs)

        if len(mshs) == self.n:
            return mshs

        if len(shs) >= self.n:
            return sorted(shs)[0:self.n]

        return None

    def _select_minshingles(self, shs):
        buckets = [None]*self.n
        for x in shs:
            bkt = x % self.n
            buckets[bkt] = x if buckets[bkt] is None else min(buckets[bkt], x)

        return filter(lambda a: a is not None, buckets)

    def _count_shingles(self, words):
        shingles = []
        for i in xrange(len(words) - self.window):
            h = mmh3.hash(' '.join(words[i:i+self.window]).encode('utf-8'))
            shingles.append(h)
        return sorted(shingles)
        # return set(sorted(shingles))

    @staticmethod
    def _extract_words(text):
        words = re.findall(MinshinglesCounter.SPLIT_RGX, text)
        return words


def main():
    files = parse_command_line().files
    reader = DocumentStreamReader(files)
    MinHashesCounter = MinshinglesCounter(window=5, n=20)

    # STEP 1
    mshs, urls = [], []

    for doc in reader:
        shingles = MinHashesCounter.count(doc.text)
        if shingles is not None:
            mshs.append(set(shingles))
            urls.append(doc.url)

    # STEP 2
    mshs_groups = {}

    for doc_i in xrange(len(urls)):
        for shingle in mshs[doc_i]:
            try:
                mshs_groups[shingle].append(doc_i)
            except KeyError:
                mshs_groups[shingle] = [doc_i]

    # STEP 3
    mshs_pairs = {}

    for doc_list in mshs_groups.values():
        for pair in combinations(doc_list, 2):
            try:
                mshs_pairs[pair] += 1
            except KeyError:
                mshs_pairs[pair] = 1

    # STEP 4
    for (doc_x, doc_y), counts in mshs_pairs.iteritems():
        # if counts > 17:
        #     print urls[doc_x], urls[doc_y], float(counts) / MinHashesCounter.n

        jaccard_measure = float(counts) / (counts + 2 * (MinHashesCounter.n - counts))
        if jaccard_measure >= .75:
            print urls[doc_x], urls[doc_y], float(counts) / MinHashesCounter.n
            # print doc_x, doc_y, float(counts) / MinHashesCounter.n

if __name__ == '__main__':
    main()
    # brute_force()
