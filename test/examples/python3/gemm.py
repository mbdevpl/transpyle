"""General Matrix-Matrix."""

import numpy as np
import static_typing as st


def dgemm(a: st.ndarray[2, np.double, (100, 100)],
          b: st.ndarray[2, np.double, (100, 100)]) -> st.ndarray[2, np.double, (100, 100)]:

    ymax = a.shape(0)  # type: np.int32
    imax = a.shape(1)  # type: np.int32
    xmax = b.shape(1)  # type: np.int32
    c: st.ndarray[2, np.double] = np.zeros((ymax, xmax), dtype=np.double)

    # pragma: acc parallel copyin(a,b) copyout(c)
    # pragma: acc loop gang
    for y in range(ymax):  # type: np.int32
        # pragma: acc loop worker
        for i in range(imax):  # type: np.int32
            # pragma: acc loop vector reduction(+: c[y][x])
            for x in range(xmax):  # type: np.int32
                c[y, x] += a[y, i] * b[i, x]
            # pragma: acc end loop
        # pragma: acc end loop
    # pragma: acc end loop
    # pragma: acc end parallel

    return c
