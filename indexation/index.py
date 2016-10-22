# -*- coding: utf-8 -*

import os

from doc2words import extract_words
from docreader import *
from coding_methods import encode


def dump_index_part(f_name, index, encoding):
    terms = {}

    with open(f_name + '.index', 'wb') as f_index:
        offset = 0
        for key, docs in index.iteritems():
            if len(docs) < 2:
                continue

            encoded_seq = encode(docs, encoding)
            f_index.write(encoded_seq)
            terms[key] = (offset, len(encoded_seq))
            offset += len(encoded_seq)

    with open(f_name + '.dict', 'w') as f_dict:
        f_dict.write(struct.pack("Q", len(terms)))
        for key, value in terms.iteritems():
            f_dict.write(struct.pack("qII", key, value[0], value[1]))


if __name__ == '__main__':
    args = parse_command_line().files
    encoding, files = args[0], args[1:]

    path = './index/'
    if not os.path.exists(path):
        os.makedirs(path)

    index, urls = {}, []

    reader = DocumentStreamReader(files)
    n_files, batch_size = 0, 5e4

    need_to_dump = False

    for doc_i, doc in enumerate(reader):
        need_to_dump = True

        urls.append(doc.url + '\n')
        terms = set(extract_words(doc.text))
        for term in terms:
            try:
                index[hash(term)].append(doc_i)
            except KeyError:
                # 0 is a fake document. This principle helps to split index into multiple files
                index[hash(term)] = [0, doc_i]

        if (doc_i + 1) % batch_size == 0:
            dump_index_part(path + 'part_{0:03d}'.format(n_files), index, encoding)
            for key in index.keys():
                # next doc will be encoded correctly
                index[key] = [index[key][-1]]
            n_files += 1
            need_to_dump = False

    if need_to_dump:
        dump_index_part(path + 'part_{0:03d}'.format(n_files), index, encoding)

    f_name = path + 'index'

    with open(f_name + '.config', 'w') as f_config:
        f_config.write(encoding)

    with open(f_name + '.urls', 'w') as f:
        f.writelines(urls)
