# -*- coding: utf-8 -*

import sys
import struct

import numpy as np

from coding_methods import decode
from query import *
from bisect import bisect_left


class TermDict:
    def __init__(self, f_name):
        self.f_name = open(f_name, 'rb')
        self.n_bins = struct.unpack("I", self.f_name.read(4))[0]
        self.bins_size = list(struct.unpack("{}I".format(self.n_bins), self.f_name.read(4 * self.n_bins)))

    @staticmethod
    def __binary_search_index(x, elem):
        i = bisect_left(x, elem)
        if i != len(x) and x[i] == elem:
            return i
        raise ValueError

    def __getitem__(self, item):
        bin_item = hash(item) % self.n_bins
        offset = sum([self.bins_size[i] * (8 + 4 + 4) for i in range(bin_item)]) + 4 + 4 * self.n_bins
        self.f_name.seek(offset)

        bin = np.asarray(struct.unpack(
            'q2I' * self.bins_size[bin_item],
            self.f_name.read((8 + 4 + 4) * self.bins_size[bin_item])
        )).reshape(-1, 3)

        idx = TermDict.__binary_search_index(bin[:, 0], hash(item))
        offset, n_bytes = bin[idx, 1], bin[idx, 2]
        return offset, n_bytes

    def __del__(self):
        self.f_name.close()


class ReverseIndex:
    def __init__(self, file_name_index, file_name_terms, encoding):
        self.f_index = open(file_name_index, 'rb')
        self.terms = TermDict(file_name_terms)
        self.encoding = encoding

    def __getitem__(self, term):
        try:
            offset, n_bytes = self.terms[term]
        except ValueError:
            return []

        self.f_index.seek(offset)
        bytes_seq = self.f_index.read(n_bytes)
        return decode(bytearray(bytes_seq), encoding=self.encoding)

    def __del__(self):
        self.f_index.close()


if __name__ == '__main__':
    path = './index/'

    with open(path + 'index.config', 'r') as f_config:
        encoding = f_config.readline()

    index = ReverseIndex(path + 'index.index', path + 'index.dict', encoding)
    with open(path + 'index.urls', 'r') as f_urls:
        urls = f_urls.readlines()
        urls = [url[:-1] for url in urls]

    query_stack = QueryStack(index, len(urls))
    queries = sys.stdin.readlines()
    for query in queries:
        print query[:-1]
        query = query_stack.compile(query)
        query = query.get_query_urls(len(urls))

        print len(query)
        for q_i in query:
            print urls[q_i]

