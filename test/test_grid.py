import random

import numpy as np
import pytest

from plutoplot.grid import Grid, normalize_slice

random.seed(23951305348253)


class TestNormaliceSlice:
    @pytest.fixture
    def dims(self):
        return tuple(random.randint(10, 1000) for _ in range(3))

    def test_empty(self, dims):
        assert normalize_slice(np.s_[:, :, :], dims) == tuple(
            slice(0, dim, 1) for dim in dims
        )

    def test_inbounds(self, dims):
        starts = tuple(random.randint(0, dim) for dim in dims)
        stops = tuple(random.randint(start, dim) for start, dim in zip(starts, dims))
        assert (
            normalize_slice(
                np.s_[starts[0] : stops[0], starts[1] : stops[1], starts[2] : stops[2]],
                dims,
            )
            == tuple(slice(start, stop, 1) for start, stop in zip(starts, stops))
        )

    def test_outofbounds(self, dims):
        with pytest.raises(IndexError):
            normalize_slice(np.s_[0 : dims[0] + 1, :, :], dims)
        with pytest.raises(IndexError):
            normalize_slice(np.s_[dims[0] :, :, :], dims)

    def test_negative(self, dims):
        starts = tuple(-random.randint(0, dim - 1) for dim in dims)
        stops = tuple(random.randint(start, 0) for start in starts)

        assert normalize_slice(
            np.s_[starts[0] : stops[0], starts[1] : stops[1], starts[2] : stops[2]],
            dims,
        ) == tuple(
            slice(dim + start, dim + stop, 1)
            for dim, start, stop in zip(dims, starts, stops)
        )

    def test_1high_slice(self, dims):
        starts = tuple(random.randint(0, dim) for dim in dims)
        stops = (
            random.randint(starts[0], dims[0]),
            starts[1] + 1,
            random.randint(starts[2], dims[2]),
        )

        assert (
            normalize_slice(
                np.s_[starts[0] : stops[0], starts[1], starts[2] : stops[2]],
                dims,
            )
            == tuple(slice(start, stop, 1) for start, stop in zip(starts, stops))
        )
