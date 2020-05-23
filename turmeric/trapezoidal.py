#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian
"""

def get_df(buf, step):
    """
    (C1, C0)

        The derivative may be written as:

        .. math::

            d(x(n+1))/dt = C1 x(n+1) + C0

        `x_lte_coeff` is the coefficient of the Local Truncation Error,
        `predict_x` is the predicted value for :math:`x` and `predict_lte_coeff`
        is the LTE coefficient for the prediction.

    :raises ValueError: if the `pv_array` is malformed.
    """
    # check if appropriate values 
    # our method needs x(n) dx(n)/dt
    if len(buf[0]) != 3:
        raise ValueError('trapezoidal method requires buffer of size 3 x 2')
    # check for x and dx values
    if buf[0][1] is None or buf[0][2] is None:
        raise ValueError('trapezoidal method requires state and derivative at current timestep')
    
    C1 = 2.0 / step
    C0 = -1.0 * (2.0 / step * buf[0][1] + buf[0][2])

    return (C1, C0)

