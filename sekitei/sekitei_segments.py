# coding: utf-8


import numpy as np
from extract_features_update import *

from sklearn.cluster import MiniBatchKMeans
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import GradientBoostingClassifier

import warnings

features_selected = None

algorithm_cluster = None
algorithm_classify = None

quota_per_cluster = None
qlinks_per_cluster = None


def create_feature_vector(features_url):
    return [float(f in features_url) for f in features_selected]


def define_segments(QLINK_URLS, UNKNOWN_URLS, QUOTA):
    warnings.simplefilter("ignore")

    N, alpha = len(QLINK_URLS) + len(UNKNOWN_URLS), .01

    features_all = []
    features_examined = []
    features_general = []

    for url in QLINK_URLS:
        features_url = extract_features_from_url(url)
        features_all.extend(features_url)
        features_examined.append(features_url)

    for url in UNKNOWN_URLS:
        features_url = extract_features_from_url(url)
        features_all.extend(features_url)
        features_general.append(features_url)

    features_all = count_features(features_all)
    global features_selected
    features_selected = choose_features(features_all, alpha * N)
    features_selected = sorted([f[0] for f in features_selected])

    X_all = np.asarray(map(create_feature_vector, features_examined + features_general))
    Y_all = np.asarray([1] * len(QLINK_URLS) + [0] * len(UNKNOWN_URLS))

    global algorithm_cluster
    n_clusters = 25
    algorithm_cluster = MiniBatchKMeans(n_clusters=n_clusters, max_iter=100)
    clusters = algorithm_cluster.fit_predict(X_all)
    clusters_examined = clusters[:len(QLINK_URLS)]

    global qlinks_per_cluster, quota_per_cluster
    qlinks_per_cluster = np.asarray(
        [float(sum(clusters_examined == c)) / sum(clusters == c) if sum(clusters == c) else 0
         for c in range(n_clusters)],
        dtype=float
    )

    # quota_per_cluster = np.asarray([sum(clusters_examined == c) for c in range(n_clusters)], dtype=float)
    # quota_per_cluster *= float(QUOTA) / len(QLINK_URLS)
    # quota_per_cluster += QUOTA * .05

    quota_per_cluster = np.asarray([sum(clusters == c) for c in range(n_clusters)], dtype=float)
    quota_per_cluster *= float(QUOTA) / clusters.shape[0]
    quota_per_cluster += QUOTA * .05

    global algorithm_classify
    # algorithm_classify = GaussianNB()
    algorithm_classify = GradientBoostingClassifier(learning_rate=0.7, n_estimators=20)
    algorithm_classify.fit(X_all, Y_all)

    # print features_selected
    # print qlinks_per_cluster


adjust = .75


def fetch_url(url):
    warnings.simplefilter("ignore")

    global quota_per_cluster, adjust

    features = extract_features_from_url(url)
    features = create_feature_vector(features)
    features = np.asarray(features).reshape(1, len(features))
    segment = algorithm_cluster.predict(features)[0]
    answer = algorithm_classify.predict(features)[0]

    # p = algorithm_classify.predict_proba(features)[0, 0]

    adjust_step = .02
    if not answer:
        # if random.random() < max(qlinks_per_cluster[segment], probability):
        # if random.random() < probability:
        # if random.random() < qlinks_per_cluster[segment] * adjust:
        if random.random() < max(qlinks_per_cluster[segment], .125) * adjust:
            adjust -= adjust_step
            answer = True
        else:
            adjust += adjust_step
            answer = False
    else:
        adjust -= adjust_step

    if answer and quota_per_cluster[segment] > 0:
        quota_per_cluster[segment] -= 1
        return True
    else:
        return False


if __name__ == '__main__':
    pass