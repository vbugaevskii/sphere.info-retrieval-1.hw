# coding: utf-8


import os
import re
import random

from urllib import unquote
from urlparse import urlparse
from collections import Counter
from operator import itemgetter


def read_urls_from_file(f_name):
    with open(f_name) as f:
        urls = f.readlines()
    return [unquote(url[:-1]).lower() for url in urls]


def write_features_to_file(features, f_name):
    with open(f_name, 'w') as f:
        for i in features:
            f.write('{}\t{}\n'.format(i[0], i[1]))


def parse_url(url):
    url_parsed = urlparse(url)
    segments = [s for s in url_parsed.path.split('/') if s != '']
    q_params = [q for q in url_parsed.query.split('&') if q != '']
    return segments, q_params


def extract_features_from_url(url):
    segments, q_params = parse_url(url)
    features = []

    if q_params:
        features += ['param_name:{}'.format(param.split('=')[0]) for param in q_params]
        features += ['param:{}'.format(param) for param in q_params]

    if len(segments) == 0:
        return features

    features.append('segments:{}'.format(len(segments)))

    categories_templates = [
        'segment_name_{}:{}',             # name of seg
        'segment_[0-9]_{}:1',             # seg consists of digits
        'segment_substr[0-9]_{}:1',       # seg has pattern <str><digits><str>
        'segment_ext_{}:{}',              # seg has an extension
        'segment_ext_substr[0-9]_{}:{}',  # seg has pattern and an extension
        'segment_len_{}:{}'               # length of seg
    ]

    for i, seg in enumerate(segments):
        features.append(categories_templates[0].format(i, seg))

        seg_name, seg_ext = os.path.splitext(seg)
        seg_ext = seg_ext[1:]            # remove dot in extension

        if re.search(r'^(\d)+$', seg_name):
            features.append(categories_templates[1].format(i))

        # pattern_1 = re.search(r'^([^\d]*)(\d+)([^\d]+)$', seg_name)
        # pattern_2 = re.search(r'^([^\d]+)(\d+)([^\d]*)$', seg_name)
        pattern = re.search(r'[^\d]+\d+[^\d]+$', seg_name)

        if pattern:
            features.append(categories_templates[2].format(i))
        if seg_ext:
            features.append(categories_templates[3].format(i, seg_ext))
        if pattern and seg_ext:
            features.append(categories_templates[4].format(i, seg_ext))
        features.append(categories_templates[5].format(i, len(seg)))

    return features


def count_features(features):
    return Counter(features).most_common()


def choose_features(features, threshold):
    return [f for f in features if f[1] > threshold]


def sort_features(features):
    return sorted(features, key=itemgetter(1), reverse=True)


def extract_features(INPUT_FILE_1, INPUT_FILE_2, OUTPUT_FILE):
    N, alpha = 1000, 0.05

    urls_examined = read_urls_from_file(INPUT_FILE_1)
    urls_general = read_urls_from_file(INPUT_FILE_2)
    urls = random.sample(urls_examined, N // 2) + random.sample(urls_general, N // 2)

    features = []
    for url in urls:
        features.extend(extract_features_from_url(url))

    features = count_features(features)
    features = choose_features(features, alpha * N)
    features = sort_features(features)
    write_features_to_file(features, OUTPUT_FILE)

if __name__ == '__main__':
    pass
