# -*- coding: utf-8 -*

import os

from docreader import *


if __name__ == '__main__':
    files = parse_command_line().files
    files = [f[:-5] for f in files]
    print files

    f_block_names = [f + '.dict' for f in files]
    f_index_names = [f + '.index' for f in files]

    f_name = './index/index'

    # If only one partion is created, then there is no need to merge file. Just rename them
    if len(files) == 1:
        os.rename(f_block_names[0], f_name + '.dict')
        os.rename(f_index_names[0], f_name + '.index')
        exit(0)

    f_blocks = [open(f, 'rb') for f in f_block_names]
    blocks = []
    for f in f_blocks:
        block_dict_len = struct.unpack("Q", f.read(8))[0]
        block_dict = list(struct.unpack("qII" * block_dict_len, f.read((8 + 4 + 4) * block_dict_len)))
        block_dict = {
            block_dict[i]: (block_dict[i+1], block_dict[i+2])
            for i in range(0, 3 * block_dict_len, 3)
        }
        blocks.append(block_dict)

    for f in f_blocks:
        f.close()

    terms = {}
    terms_keys = reduce(lambda x, y: x | y, [set(block.keys()) for block in blocks])

    f_indexes = [open(f, 'rb') for f in f_index_names]

    with open(f_name + '.index', 'wb') as f_index:
        term_offset = 0
        for key in terms_keys:
            term_length = 0

            for i, block in enumerate(blocks):
                try:
                    offset, n_bytes = block[key]

                    f_indexes[i].seek(offset)
                    encoded_seq = f_indexes[i].read(n_bytes)

                    f_index.write(encoded_seq)
                    term_length += len(encoded_seq)
                except KeyError:
                    pass

            terms[key] = (term_offset, term_length)
            term_offset += term_length

    for f in f_indexes:
        f.close()

    with open(f_name + '.dict', 'w') as f_dict:
        f_dict.write(struct.pack("Q", len(terms)))
        for key, value in terms.iteritems():
            f_dict.write(struct.pack("qII", key, value[0], value[1]))

    for f in f_block_names + f_index_names:
        os.remove(f)