#!/usr/bin/env python3

import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('limit', type=int)
    parser.add_argument('width', type=int)
    parser.add_argument('height', type=int)

    args = parser.parse_args()

    limit = args.limit
    width = args.width
    height = args.height

    # print('{} times {} x {}'.format(limit, width, height))

    a = [1] * (width * height)
    b = [1] * (height * width)
    c = None

    for n in range(0, limit):
        c = [0] * (height * height)
        for y in range(0, height):
            a_index_part = y * width
            c_index_part = y * height
            for i in range(0, width):
                a_index = i + a_index_part
                b_index_part = i * height
                for x in range(0, height):
                    c[x + c_index_part] += a[a_index] * b[x + b_index_part]

    if limit > 0:
        for y in range(0, height):
            c_index_part = y * height
            for x in range(0, height):
                if c[x + c_index_part] != height:
                    print('{} - error at {} x {}'.format(c[x + c_index_part], x, y))
                    exit(2)
