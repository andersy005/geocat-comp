from . import _ncomp
import numpy as np
import xarray as xr
from dask.array.core import map_blocks

def linint2(fi, xo, yo, icycx, xmsg=None, meta=True, xi=None, yi=None):
    """Interpolates a regular grid to a rectilinear one using bi-linear
    interpolation.

    Args:

        fi (:class:`xarray.DataArray` or :class:`numpy.ndarray`):
            An array of two or more dimensions. If xi is passed in as an
            argument, then the size of the rightmost dimension of fi must
            match the rightmost dimension of xi. Similarly, if yi is
            passed in as an argument, then the size of the second-
            rightmost dimension of fi must match the rightmost dimension
            of yi.

            Note:

                This variable must be
                supplied as a :class:`xarray.DataArray` in order to copy the
                dimension names to the output.  Otherwise, default names will
                be used.

        xo (:class:`xarray.DataArray` or :class:`numpy.ndarray`):
            A one-dimensional array that specifies the X coordinates of the
            return array. It must be strictly monotonically increasing, but
            may be unequally spaced.

            For geo-referenced data, xo is generally the longitude array.

        yo (:class:`xarray.DataArray` or :class:`numpy.ndarray`):
            A one-dimensional array that specifies the Y coordinates of the
            return array. It must be strictly monotonically increasing, but
            may be unequally spaced.

            For geo-referenced data, yo is generally the latitude array.

        icycx (:obj:`bool`):
            An option to indicate whether the rightmost dimension of fi is
            cyclic. This should be set to True only if you have global data,
            but your longitude values don't quite wrap all the way around the
            globe. For example, if your longitude values go from, say, -179.75
            to 179.75, or 0.5 to 359.5, then you would set this to True.

        meta (:obj:`bool`):
            Set to False to disable metadata; default is True.

        xi (:class:`numpy.ndarray`):
            An array that specifies the X coordinates of the fi array. Most
            frequently, this is a 1D strictly monotonically increasing array
            that may be unequally spaced. In some cases, xi can be a multi-
            dimensional array (see next paragraph). The rightmost dimension
            (call it nxi) must have at least two elements, and is the last
            (fastest varying) dimension of fi.

            If xi is a multi-dimensional array, then each nxi subsection of xi
            must be strictly monotonically increasing, but may be unequally
            spaced. All but its rightmost dimension must be the same size as
            all but fi's rightmost two dimensions.

            For geo-referenced data, xi is generally the longitude array.

            Note:
                If left unspecified, the rightmost coordinate dimension of fi
                will be used. This parameter must be specified as a keyword
                argument.

        yi (:class:`numpy.ndarray`):
            An array that specifies the Y coordinates of the fi array. Most
            frequently, this is a 1D strictly monotonically increasing array
            that may be unequally spaced. In some cases, yi can be a multi-
            dimensional array (see next paragraph). The rightmost dimension
            (call it nyi) must have at least two elements, and is the second-
            to-last dimension of fi.

            If yi is a multi-dimensional array, then each nyi subsection of yi
            must be strictly monotonically increasing, but may be unequally
            spaced. All but its rightmost dimension must be the same size as
            all but fi's rightmost two dimensions.

            For geo-referenced data, yi is generally the latitude array.

            Note:
                If left unspecified, the second-to-rightmost coordinate
                dimension of fi will be used. This parameter must be specified
                as a keyword argument.

    Returns:

        :class:`xarray.DataArray`: The interpolated grid. If the *meta*
        parameter is True, then the result will include named dimensions
        matching the input array. The returned value will have the same
        dimensions as fi, except for the rightmost two dimensions which
        will have the same dimension sizes as the lengths of yo and xo.
        The return type will be double if fi is double, and float otherwise. 

    Examples:

        Example 1: Using linint2 with :class:`xarray.DataArray` input

        .. code-block:: python

            import numpy as np
            import xarray as xr
            import geocat.comp

            fi_np = np.random.rand(30, 80)  # random 30x80 array

            # xi and yi do not have to be equally spaced, but are in this example
            xi = np.arange(80)
            yi = np.arange(30)

            # create target coordinate arrays, in this case using the same
            # min/max values as xi and yi, but with different spacing
            xo = np.linspace(xi.min(), xi.max(), 100)
            yo = np.linspace(yi.min(), yi.max(), 50)

            # create :class:`xarray.DataArray` and chunk it using the full shape of the original array
            # note that xi and yi are attached as coordinate arrays
            fi = xr.DataArray(fi_np, dims=['lat', 'lon'], coords={'lat': yi, 'lon': xi}).chunk(fi_np.shape)

            fo = geocat.comp.linint2(fi, xo, yo, 0)

    """

    if xmsg is None:
        xmsg = _ncomp.dtype_default_fill[fi.dtype]

    if xi is None:
        xi = fi.coords[fi.dims[-1]].values
    if yi is None:
        yi = fi.coords[fi.dims[-2]].values
    fi_data = fi.data
    fo_chunks = list(fi.chunks)
    fo_chunks[-2:] = (yo.shape, xo.shape)
    fo = map_blocks(_ncomp._linint2, xi, yi, fi_data, xo, yo, icycx, xmsg, chunks=fo_chunks, dtype=fi.dtype, drop_axis=[fi.ndim-2, fi.ndim-1], new_axis=[fi.ndim-2, fi.ndim-1])

    result = fo.compute()

    if meta:
        coords = {k:v if k not in fi.dims[-2:] else (xo if k == fi.dims[-1] else yo) for (k, v) in fi.coords.items()}
        result = xr.DataArray(result, attrs=fi.attrs, dims=fi.dims, coords=coords)
    else:
        result = xr.DataArray(result)

    return result
