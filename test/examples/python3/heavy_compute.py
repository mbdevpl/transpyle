
import numpy as np
import static_typing as st

N = st.generic.GenericVar()


def heavy_compute(input_data: st.ndarray[1, np.double, (N,)]) -> st.ndarray[1, np.double, (N,)]:
    output_data = np.zeros((input_data.size,), dtype=np.double)
    # t y p e: st.ndarray[1, np.double] # TMP skipping because of return type information

    # pragma: acc parallel loop
    # pragma: omp parallel do
    for i in range(input_data.size):  # type: int
        output_data[i] = 1
        for _ in range(10240):  # type: int
            output_data[i] = output_data[i] / input_data[i]
        for _ in range(10240):  # type: int
            output_data[i] = output_data[i] * input_data[i]
        for _ in range(10240):  # type: int
            output_data[i] = output_data[i] / input_data[i]
        for _ in range(10240):  # type: int
            output_data[i] = output_data[i] * input_data[i]
    # pragma: omp end parallel do

    return output_data
