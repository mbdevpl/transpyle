"""General Matrix-Matrix."""

import numpy as np
import static_typing as st

def dgemm(a: st.ndarray[2, np.double, (100, 100)],
          b: st.ndarray[2, np.double, (100, 100)]) -> st.ndarray[2, np.double, (100, 100)]:

    y_max: np.int32 = a.shape(0)
    i_max: np.int32 = a.shape(1)
    x_max: np.int32 = b.shape(1)
    c: st.ndarray[2, np.double] = np.zeros((y_max, x_max), dtype=np.double)

    for y in range(y_max): # type: np.int32
        for i in range(i_max): # type: np.int32
            for x in range(x_max): # type: np.int32
                c[y, x] += a[y, i] * b[i, x]

    return c
