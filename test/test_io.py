import unittest
import os
import numpy as np
from plutoplot.grid import Grid
from generate_testdata import generate_gridfile

class TestGrid(unittest.TestCase):

    def setUp(self):
        self.file = 'gridtest.out'
        self.dims = (10, 11, 12)
        generate_gridfile(self.file, self.dims)
        self.grid = Grid(self.file)

    def tearDown(self):
        os.remove(self.file)

    def testDimensions(self):
        self.assertEqual(self.dims, self.grid.dims)
        self.assertEqual(self.dims, self.grid.data_shape)

    def testData(self):
        for i, res in enumerate(self.dims, start=1):
            x = getattr(self.grid, f'x{i}')
            dx = getattr(self.grid, f'dx{i}')
            np.testing.assert_array_almost_equal_nulp(x, np.arange(0.5, res, 1))
            np.testing.assert_array_almost_equal_nulp(dx, np.ones(res))


if __name__ == '__main__':
    unittest.main()
