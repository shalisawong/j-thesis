from numpy import array
from numpy import float as npfloat
from ghmm import HMMFromMatrices, Float, GaussianDistribution

def uniformMatrix(c, r, v=0):
	"""
	Create a c x r matrix filled with the value v
	"""
	matrix = []
	for i in range(0, r):
		matrix.append([0]*c)

	return array(matrix, npfloat)

def blockDiagMatrix(matrices):
	"""
	Given matrices A_1, A_2, ... A_n, create the matrix:

	A_1	  ...	    0
	.	A_2			.
	.		... 	.
	. 				.

	0	  	  ... A_n
	"""
	ydim = 0
	xdim = 0

	for matrix in matrices:
		ydim += len(matrix)
		xdim += len(matrix[0])

	block_diag = uniformMatrix(xdim, ydim)
	x_offset = 0
	y_offset = 0

	for matrix in matrices:
		ydim_m = len(matrix)
		xdim_m = len(matrix[0])
		for y in range(0, ydim_m,):
			for x in range(0, xdim_m):
				block_diag[y+y_offset][x+x_offset] = matrix[y][x]

		x_offset += xdim_m
		y_offset += ydim_m

	return block_diag
