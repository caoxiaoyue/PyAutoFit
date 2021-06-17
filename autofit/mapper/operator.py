
from abc import ABC, abstractmethod
from functools import wraps
from typing import Tuple

import numpy as np
from scipy.linalg import cho_factor, solve_triangular, get_blas_funcs, block_diag
from scipy._lib._util import _asarray_validated

from autofit.graphical.utils import cached_property


class LinearOperator(ABC):
    @abstractmethod
    def __mul__(self, x: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def __rtruediv__(self, x: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def __rmul__(self, x: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def ldiv(self, x: np.ndarray) -> np.ndarray:
        pass

    @property
    @abstractmethod
    def shape(self) -> Tuple[int, ...]:
        pass

    def __len__(self) -> int:
        return self.shape[0]

    @property
    def size(self) -> int:
        return np.prod(self.shape, dtype=int)

    @property
    def lshape(self):
        return self.shape[:1]
    
    @property 
    def rshape(self):
        return self.shape[1:]

    @cached_property
    @abstractmethod
    def log_det(self):
        pass

    def quad(self, M: np.ndarray) -> np.ndarray:
        return (M * self).T * self

    def invquad(self, M: np.ndarray) -> np.ndarray:
        return (M / self).T / self

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        if ufunc is np.multiply:
            return self.__rmul__(inputs[0])
        elif ufunc is np.divide:
            return self.__rtruediv__(inputs[0])
        elif ufunc is np.matmul:
            return self.__rmul__(inputs[0])
        else:
            return NotImplemented


class MatrixOperator(LinearOperator):

    def __init__(self, M: np.ndarray):
        self.M = M

    @property
    def shape(self):
        return self.M.shape

    @cached_property
    def log_det(self):
        return np.linalg.slogdet(self.M)[1]

    def __mul__(self, x: np.ndarray) -> np.ndarray:
        return self.M.dot(x)

    def __rtruediv__(self, x: np.ndarray) -> np.ndarray:
        return np.linalg.solve(self.M.T, x.T)

    def __rmul__(self, x: np.ndarray) -> np.ndarray:
        return np.dot(x, self.M)

    def ldiv(self, x: np.ndarray) -> np.ndarray:
        return np.linalg.solve(self.M, x)

    def to_dense(self):
        return self.M


class IdentityOperator(LinearOperator):
    def __init__(self):
        pass

    def _identity(self, values: np.ndarray) -> np.ndarray:
        return values

    __mul__ = _identity
    __rtruediv__ = _identity
    __rmul__ = _identity
    ldiv = _identity
    rdiv = __rtruediv__
    rmul = __rmul__
    lmul = __mul__
    __matmul__ = __mul__
    quad = _identity
    invquad = _identity

    @property
    def log_det(self):
        return 0.

    @property
    def shape(self):
        return ()

    def __len__(self):
        return 0


def _mul_triangular(c, b, trans=False, lower=True, overwrite_b=False,
                    check_finite=True):
    """wrapper for BLAS function trmv to perform triangular matrix
    multiplications


    Parameters
    ----------
    a : (M, M) array_like
        A triangular matrix
    b : (M,) or (M, N) array_like
        vector/matrix being multiplied
    lower : bool, optional
        Use only data contained in the lower triangle of `a`.
        Default is to use upper triangle.
    trans : bool, optional
        type of multiplication,

        ========  =========
        trans     system
        ========  =========
        False     a b
        True      a^T b
    overwrite_b : bool, optional
        Allow overwriting data in `b` (may enhance performance)
        not fully tested
    check_finite : bool, optional
        Whether to check that the input matrices contain only finite numbers.
        Disabling may give a performance gain, but may result in problems
        (crashes, non-termination) if the inputs do contain infinities or NaNs.
    """
    a1 = _asarray_validated(c, check_finite=check_finite)
    b1 = _asarray_validated(b, check_finite=check_finite)

    n = c.shape[1]
    if c.shape[0] != n:
        raise ValueError("Triangular matrix passed must be square")
    if b.shape[0] != n:
        raise ValueError(
            f"shapes {c.shape} and {b.shape} not aligned: "
            f"{n} (dim 1) != {b.shape[0]} (dim 0)")

    trmv, = get_blas_funcs(('trmv',), (a1, b1))
    if a1.flags.f_contiguous:
        def _trmv(a1, b1, overwrite_x):
            return trmv(
                a1, b1,
                lower=lower, trans=trans, overwrite_x=overwrite_x)
    else:
        # transposed system is solved since trmv expects Fortran ordering
        def _trmv(a1, b1, overwrite_x=overwrite_b):
            return trmv(
                a1.T, b1,
                lower=not lower, trans=not trans, overwrite_x=overwrite_x)

    if b1.ndim == 1:
        return _trmv(a1, b1, overwrite_b)
    elif b1.ndim == 2:
        # trmv only works for vector multiplications
        # set Fortran order so memory contiguous
        b2 = np.array(b1, order='F')
        for i in range(b2.shape[1]):
            # overwrite results
            _trmv(a1, b2[:, i], True)

        if overwrite_b:
            b1[:] = b2
            return b1
        else:
            return b2
    else:
        raise ValueError("b must have 1 or 2 dimensions, has {b.ndim}")


# TODO refactor these for non-square transformations

def _wrap_leftop(method):
    @wraps(method)
    def leftmethod(self, x: np.ndarray) -> np.ndarray:
        x = np.asanyarray(x)
        return method(self, x.reshape(*self.rshape, -1)).reshape(x.shape)

    return leftmethod


def _wrap_rightop(method):
    @wraps(method)
    def rightmethod(self, x: np.ndarray) -> np.ndarray:
        x = np.asanyarray(x)
        return method(self, x.reshape(-1, *self.lshape)).reshape(x.shape)

    return rightmethod


class CholeskyOperator(LinearOperator):
    """ This performs the whitening transforms for the passed
    cholesky factor of the Hessian/inverse covariance of the system.

    see https://en.wikipedia.org/wiki/Whitening_transformation

    >>> M = CholeskyTransform(linalg.cho_factor(hess))
    >>> y = M * x
    >>> f, df_dx = func_and_gradient(M.ldiv(y))
    >>> df_dy = df_df * M
    >>> 
    """

    def __init__(self, cho_factor):
        self.c, self.lower = self.cho_factor = cho_factor
        self.L = self.c if self.lower else self.c.T
        self.U = self.c.T if self.lower else self.c

    @classmethod
    def from_dense(cls, hess):
        return cls(cho_factor(hess))

    @_wrap_leftop
    def __mul__(self, x):
        return _mul_triangular(self.U, x, lower=False)

    @_wrap_rightop
    def __rmul__(self, x):
        return _mul_triangular(self.L, x.T, lower=True).T

    @_wrap_rightop
    def __rtruediv__(self, x):
        return solve_triangular(self.L, x.T, lower=True).T

    @_wrap_leftop
    def ldiv(self, x):
        return solve_triangular(self.U, x, lower=False)

    @cached_property
    def log_det(self):
        return np.sum(np.log(self.U.diagonal()))

    rdiv = __rtruediv__
    rmul = __rmul__
    lmul = __mul__
    __matmul__ = __mul__

    @property
    def shape(self):
        return self.c.shape

    def to_dense(self):
        return np.tril(self.L) @ np.triu(self.U)


class InverseLinearOperator(LinearOperator):
    def __init__(self, transform):
        self.transform = transform

    @abstractmethod
    def __mul__(self, x: np.ndarray) -> np.ndarray:
        return x / self.transform

    @abstractmethod
    def __rtruediv__(self, x: np.ndarray) -> np.ndarray:
        return self.transform * x

    @abstractmethod
    def __rmul__(self, x: np.ndarray) -> np.ndarray:
        return self.transform.ldiv(x)

    @abstractmethod
    def ldiv(self, x: np.ndarray) -> np.ndarray:
        return x * self.transform

    @property
    def shape(self) -> Tuple[int, ...]:
        return self.transform.shape

    @cached_property
    def log_det(self):
        return - self.transform.log_det

    def to_dense(self):
        return np.linalg.inv(self.transform.to_dense())


class InvCholeskyTransform(CholeskyOperator):
    """In the case where the covariance matrix is passed
    we perform the inverse operations
    """
    __mul__ = CholeskyOperator.__rtruediv__
    __rmul__ = CholeskyOperator.ldiv
    __rtruediv__ = CholeskyOperator.__mul__
    ldiv = CholeskyOperator.__rmul__

    rdiv = __rtruediv__
    rmul = __rmul__
    lmul = __mul__
    __matmul__ = __mul__

    @cached_property
    def log_det(self):
        return - np.sum(np.log(self.U.diagonal()))

    def to_dense(self):
        return solve_triangular(self.U, np.triul(self.L), lower=False)



class DiagonalMatrix(LinearOperator):
    def __init__(self, scale, inv_scale=None):
        self.scale = np.ravel(scale)
        self.inv_scale = 1 / \
            scale if inv_scale is None else np.ravel(inv_scale)

    @_wrap_leftop
    def __mul__(self, x):
        return self.scale[:, None] * x

    @_wrap_rightop
    def __rmul__(self, x):
        return x * self.scale

    @_wrap_rightop
    def __rtruediv__(self, x):
        return x * self.inv_scale

    @_wrap_leftop
    def ldiv(self, x):
        return self.inv_scale[:, None] * x

    @cached_property
    def log_det(self):
        return np.sum(np.log(self.scale))

    rdiv = __rtruediv__
    rmul = __rmul__
    lmul = __mul__
    __matmul__ = __mul__

    @property
    def shape(self):
        return self.scale.shape * 2

    @cached_property
    def log_scale(self):
        return np.log(self.scale)

    def to_dense(self):
        return np.diag(self.scale)


class VecOuterProduct(LinearOperator):
    """
    represents the matrix vector outer product
    
    outer = vec[:, None] * vecT[None, :]
    """
    def __init__(self, vec, vecT=None):
        self.vec = np.ravel(vec)[:, None]
        self.vecT = np.ravel(vec if vecT is None else vecT)[None, :]
        
    @_wrap_leftop
    def __mul__(self, x):
        return self.vec @ self.vecT.dot(x)
        
    @_wrap_rightop
    def __rmul__(self, x):
        return x.dot(self.vec) @ self.vecT
    
    def __rtruediv__(self, x):
        raise NotImplementedError()

    def ldiv(self, x):
        raise NotImplementedError()

    @cached_property
    def log_det(self):
        return - np.inf

    rdiv = __rtruediv__
    rmul = __rmul__
    lmul = __mul__
    __matmul__ = __mul__
    __rmatmul__ = __rmul__
    
    @property
    def shape(self):
        return (self.vec.size, self.vecT.size)

    def to_dense(self):
        return np.outer(self.vec, self.vecT)
    

class MultiVecOuterProduct(LinearOperator):
    """
    represents the matrix vector outer product for stacked vectors,
    
    outer -> block_diag(*
        (v[:, None] * u[None, :] for v, u in zip(vec, vecT)
    )
    outer @ x -> np.vstack([
        v[:, None] * u[None, :] @ x for v, u in zip(vec, vecT)
    ])
    """
    def __init__(self, vec, vecT=None):
        self.vec = np.asanyarray(vec)
        self.vecT = np.asanyarray(vec if vecT is None else vecT)
        self.n, self.d = self.vec.shape
        self.nT, self.dT = self.vecT.shape
        
    @_wrap_leftop
    def __mul__(self, x):
        return np.einsum(
            "ij,ik,ikl -> ijl",
            self.vec, self.vecT, x
        )
        
    @_wrap_rightop
    def __rmul__(self, x):
        return np.einsum(
            "ij,ik,lij -> lik",
            self.vec, self.vecT, x
        )
    
    def __rtruediv__(self, x):
        raise NotImplementedError()

    def ldiv(self, x):
        raise NotImplementedError()

    @cached_property
    def log_det(self):
        return - np.inf

    rdiv = __rtruediv__
    rmul = __rmul__
    lmul = __mul__
    __matmul__ = __mul__
    __rmatmul__ = __rmul__
    
    @property
    def shape(self):
        return (self.n, self.d, self.nT, self.dT)
    
    @property
    def lshape(self):
        return self.shape[:2]
    
    @property 
    def rshape(self):
        return self.shape[2:]

    def to_dense(self):
        return block_diag(*(
            self.vec[:, :, None] * self.vecT[:, None, :]
        ))


class ShermanMorrison(LinearOperator):
    """
    Represents the Sherman-Morrison low rank update, 
    inv(A + vec @ vec.T) = 
        inv(A) - inv(A) @ vec @ vec.T @ inv(A) / (1 + vec @ inv(A) @ vec/T)
    """
    def __init__(self, linear, vec):
        self.linear = linear
        if np.ndim(vec) == 2:
            self.outer = MultiVecOuterProduct(vec)
        elif np.ndim(vec) == 1:
            self.outer = VecOuterProduct(vec)
        else: 
            raise ValueError("vec must be 1 or 2 dimensional")
            
        self.inv_scale = 1 + linear.quad(vec.ravel())
        
    @_wrap_leftop
    def __mul__(self, x):
        return self.linear * x + self.outer * x
    
    @_wrap_rightop
    def __rmul__(self, x):
        return x * self.linear + x * self.outer
    
    @_wrap_rightop
    def __rtruediv__(self, x):
        x1 = x / self.linear
        return x1 - ((x1/self.inv_scale) * self.outer) / self.linear

    @_wrap_leftop
    def ldiv(self, x):
        x1 = self.linear.ldiv(x)
        return x1 - self.linear.ldiv(self.outer.dot(x1/self.inv_scale))
    
    @cached_property
    def log_det(self):
        return self.linear.log_det + np.log(self.inv_scale)
    
    @property
    def shape(self):
        return self.linear.shape
    
    rdiv = __rtruediv__
    rmul = __rmul__
    lmul = __mul__
    __matmul__ = __mul__
    __rmatmul__ = __rmul__

    def to_dense(self):
        dense_outer = self.outer.to_dense()
        return self.linear.to_dense().reshape(dense_outer.shape) + dense_outer
