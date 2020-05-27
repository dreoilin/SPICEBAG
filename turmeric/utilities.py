import numpy as np

import functools

from . import options

def convergence_check(x, dx, residuum, nv_minus_one, debug=False):
    """Perform a convergence check

    **Parameters:**

    x : array-like
        The results to be checked.
    dx : array-like
        The last increment from a Newton-Rhapson iteration, solving
        ``F(x) = 0``.
    residuum : array-like
        The remaining error, ie ``F(x) = residdum``
    nv_minus_one : int
        Number of voltage variables in x. If ``nv_minus_one`` is equal to
        ``n``, it means ``x[:n]`` are all voltage variables.
    debug : boolean, optional
        Whether extra information is needed for debug purposes. Defaults to
        ``False``.

    **Returns:**

    chk : boolean
        Whether the check was passed or not. ``True`` means 'convergence!'.
    rbn : ndarray
        The convergence check results by node, if ``debug`` was set to ``True``,
        else ``None``.
    """
    if not hasattr(x, 'shape'):
        x = np.array(x)
        dx = np.array(dx)
        residuum = np.array(residuum)
    vcheck, vresults = custom_convergence_check(x[:nv_minus_one, 0], dx[:nv_minus_one, 0], residuum[:nv_minus_one, 0], er=options.ver, ea=options.vea, eresiduum=options.iea)
    icheck, iresults = custom_convergence_check(x[nv_minus_one:], dx[nv_minus_one:], residuum[nv_minus_one:], er=options.ier, ea=options.iea, eresiduum=options.vea)
    return vcheck and icheck, vresults + iresults

def custom_convergence_check(x, dx, residuum, er, ea, eresiduum, debug=False):
    """Perform a custom convergence check

    **Parameters:**

    x : array-like
        The results to be checked.
    dx : array-like
        The last increment from a Newton-Rhapson iteration, solving
        ``F(x) = 0``.
    residuum : array-like
        The remaining error, ie ``F(x) = residdum``
    ea : float
        The value to be employed for the absolute error.
    er : float
        The value for the relative error to be employed.
    eresiduum : float
        The maximum allowed error for the residuum (left over error).
    debug : boolean, optional
        Whether extra information is needed for debug purposes. Defaults to
        ``False``.

    **Returns:**

    chk : boolean
        Whether the check was passed or not. ``True`` means 'convergence!'.
    rbn : ndarray
        The convergence check results by node, if ``debug`` was set to ``True``,
        else ``None``.
    """
    all_check_results = []
    if not hasattr(x, 'shape'):
        x = np.array(x)
        dx = np.array(dx)
        residuum = np.array(residuum)
    if x.shape[0]:
        if not debug:
            ret = np.allclose(x, x + dx, rtol=er, atol=ea) and \
                  np.allclose(residuum, np.zeros(residuum.shape),
                              atol=eresiduum, rtol=0)
        else:
            for i in range(x.shape[0]):
                if np.abs(dx[i, 0]) < er*np.abs(x[i, 0]) + ea and \
                   np.abs(residuum[i, 0]) < eresiduum:
                    all_check_results.append(True)
                else:
                    all_check_results.append(False)
                if not all_check_results[-1]:
                    break

            ret = not (False in all_check_results)
    else:
        # We get here when there's no variable to be checked. This is because
        # there aren't variables of this type.  Eg. the circuit has no voltage
        # sources nor voltage defined elements. In this case, the actual check
        # is done only by current_convergence_check, voltage_convergence_check
        # always returns True.
        ret = True

    return ret, all_check_results

class memoized(object):
    '''
    From https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
    Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args):
        if not isinstance(args, list):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
        return value

    def __repr__(self):
       '''Return the function's docstring.'''
       return self.func.__doc__

    def __get__(self, obj, objtype):
       '''Support instance methods.'''
       return functools.partial(self.__call__, obj)
