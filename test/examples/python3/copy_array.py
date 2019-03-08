
import numpy as np
import static_typing as st

N = st.generic.GenericVar()


def copy_array(input_data: st.ndarray[1, np.double, (N,)]) -> st.ndarray[1, np.double, (N,)]:
    output_data = np.zeros((input_data.size,), dtype=np.double)
    # t y p e: st.ndarray[1, np.double] # TMP skipping because of return type information
    for i in range(input_data.size):  # type: int
        output_data[i] = input_data[i]
    return output_data
