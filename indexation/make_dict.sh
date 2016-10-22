#!/bin/bash

python ./merge_index.py ./index/part_*.dict
python ./make_dict.py
