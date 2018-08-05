"""General Matrix-Matrix."""

import numpy as np
import static_typing as st


def dgemm(a: st.ndarray[2, np.double, (100, 100)],
          b: st.ndarray[2, np.double, (100, 100)]) -> st.ndarray[2, np.double, (100, 100)]:

    y_max = a.shape(0)  # type: np.int32
    i_max = a.shape(1)  # type: np.int32
    x_max = b.shape(1)  # type: np.int32
    c = np.zeros((y_max, x_max), np.double)
    # : st.ndarray[2, np.double, (100, 100)]

    #pragma omp for
    for y in range(y_max):  # type: np.int32
        for i in range(i_max):  # type: np.int32
            for x in range(x_max):  # type: np.int32
                c[y, x] += a[y, i] * b[i, x]

    return c
