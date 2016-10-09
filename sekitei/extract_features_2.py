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
    features = dict()

    if q_params:
        features['param_name'] = [param.split('=')[0] for param in q_params]
        features['param'] = q_params

    if len(segments) == 0:
        return features

    features['segments'] = len(segments)

    categories_templates = [
        'segment_name_{}',              # name of seg
        'segment_[0-9]_{}',             # seg consists of digits
        'segment_substr[0-9]_{}',       # seg has pattern <str><digits><str>
        'segment_ext_{}',               # seg has an extension
        'segment_ext_substr[0-9]_{}',   # seg has pattern and an extension
        'segment_len_{}'                # length of seg
    ]

    for i, seg in enumerate(segments):
        categories = [cat.format(i) for cat in categories_templates]
        features[categories[0]] = seg

        seg_name, seg_ext = os.path.splitext(seg)
        seg_ext = seg_ext[1:]            # remove dot in extension

        if re.search(r'^(\d)+$', seg_name):
            features[categories[1]] = 1

        # pattern_1 = re.search(r'^([^\d]*)(\d+)([^\d]+)$', seg_name)
        # pattern_2 = re.search(r'^([^\d]+)(\d+)([^\d]*)$', seg_name)
        pattern = re.search(r'[^\d]+\d+[^\d]+$', seg_name)

        if pattern:
            features[categories[2]] = 1
        if seg_ext:
            features[categories[3]] = seg_ext
        if pattern and seg_ext:
            features[categories[4]] = seg_ext
        features[categories[5]] = len(seg)

    return features


def features_union(features):
    keys = [set(d.keys()) for d in features]
    keys = set.union(*keys)
    f = {k: [d[k] for d in features if k in d.keys()]
         for k in keys if k not in ['param_name', 'param']}

    for k in ['param_name', 'param']:
        feature_ = [d[k] for d in features if k in d.keys()]
        feature_ = [j for i in feature_ for j in i]
        if feature_:
            f[k] = feature_

    return f


def count_features(features):
    features_counted = []

    for key in features.keys():
        counts = Counter(features[key])
        features_counted.append({'{}:{}'.format(key, values): counts[values] for values in counts.keys()})

    features_ = features_counted[0].copy()
    for f in features_counted[1:]:
        features_.update(f)

    return features_


def choose_features(features_, threshold):
    return {k: features_[k] for k in features_.keys() if features_[k] > threshold}


def sort_features(features):
    return sorted(features.items(), key=itemgetter(1), reverse=True)


def extract_features(INPUT_FILE_1, INPUT_FILE_2, OUTPUT_FILE):
    N, alpha = 1000, 0.05

    urls_examined = read_urls_from_file(INPUT_FILE_1)
    urls_general = read_urls_from_file(INPUT_FILE_2)
    urls = random.sample(urls_examined, N // 2) + random.sample(urls_general, N // 2)

    features = map(extract_features_from_url, urls)
    features = features_union(features)
    features = count_features(features)
    features = choose_features(features, alpha * N)
    features = sort_features(features)
    write_features_to_file(features, OUTPUT_FILE)

if __name__ == '__main__':
    pass
