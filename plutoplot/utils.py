import numpy as np

def load_binary(path, shape: tuple=(-1,), dtype_bytes=8, endianness: str='<'):
    raw = np.fromfile(path, dtype=f'{endianness}f{dtype_bytes}')
    return raw.reshape(shape)
