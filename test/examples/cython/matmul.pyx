import argparse
import cython
import array
import sys

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('limit', type=int)
    parser.add_argument('width', type=int)
    parser.add_argument('height', type=int)

    args = parser.parse_args()

    cdef int limit = args.limit
    cdef int width = args.width
    cdef int height = args.height

    print("{} times {} x {}".format(limit, width, height))

    a = array.array('i', [0] * width * height)
    b = array.array('i', [0] * height * width)
    c = array.array('i', [0] * height * height)

    for cdef int n in range(0, limit):
        for cdef int y in range(0, height):
            a_index_part = y * width
            c_index_part = y * height
            for i in range(0, width):
                a_index = i + a_index_part
                b_index_part = i * height
                for x in range(0, height):
                    c[x + c_index_part] += a[a_index] * b[x + b_index_part];

    for y in range(0, height):
        c_index_part = y * height
        for x in range(0, height):
            if c[x + c_index_part] != 0:
                exit(2)
