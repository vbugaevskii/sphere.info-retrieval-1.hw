import struct

from collections import Counter
from operator import itemgetter


def compress_terms_dictionary(dict_, f_name, n_bins=2048):
    bins_for_keys = [(key, key % n_bins) for key in dict_.keys()]
    bins_size = Counter([b[1] for b in bins_for_keys])
    bins_size = sorted(bins_size.items(), key=itemgetter(0))
    bins_size = [b[1] for b in bins_size]

    with open(f_name, 'wb') as f_dict:
        f_dict.write(struct.pack('I', n_bins))

        for bs in bins_size:
            f_dict.write(struct.pack('I', bs))

        for bin in range(n_bins):
            keys_in_bins = sorted([b[0] for b in bins_for_keys if b[1] == bin])
            for key in keys_in_bins:
                f_dict.write(struct.pack('q2I', key, dict_[key][0], dict_[key][1]))


if __name__ == '__main__':
    f_name = './index/index.dict'
    with open(f_name, 'r') as f_dict:
        terms_len = struct.unpack("Q", f_dict.read(8))[0]
        terms = list(struct.unpack("qII" * terms_len, f_dict.read((8 + 4 + 4) * terms_len)))
        terms = {
            terms[i]: (terms[i + 1], terms[i + 2])
            for i in range(0, 3 * terms_len, 3)
        }

    compress_terms_dictionary(terms, f_name, 4096)