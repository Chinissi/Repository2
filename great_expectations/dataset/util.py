# Utility methods for dealing with DataSet objects

import numpy as np
from scipy import stats
import pandas as pd
import warnings

from functools import wraps

class DotDict(dict):
    """dot.notation access to dictionary attributes"""
    def __getattr__(self, attr):
        return self.get(attr)
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__
    def __dir__(self):
        return self.keys()


class DocInherit(object):
    """
    Docstring inheriting method descriptor

    The class itself is also used as a decorator
    doc_inherit decorator

    Usage:

    class Foo(object):
        def foo(self):
            "Frobber"
            pass

    class Bar(Foo):
        @doc_inherit
        def foo(self):
            pass

    Now, Bar.foo.__doc__ == Bar().foo.__doc__ == Foo.foo.__doc__ == "Frobber"
    # From here: https://stackoverflow.com/questions/2025562/inherit-docstrings-in-python-class-inheritance

    """

    def __init__(self, mthd):
        self.mthd = mthd
        self.name = mthd.__name__

    def __get__(self, obj, cls):
        if obj is not None:
            return self.get_with_inst(obj, cls)
        else:
            return self.get_no_inst(cls)

    def get_with_inst(self, obj, cls):

        overridden = getattr(super(cls, obj), self.name, None)

        @wraps(self.mthd, assigned=('__name__', '__module__'))
        def f(*args, **kwargs):
            return self.mthd(obj, *args, **kwargs)

        return self.use_parent_doc(f, overridden)

    def get_no_inst(self, cls):

        for parent in cls.__mro__[1:]:
            overridden = getattr(parent, self.name, None)
            if overridden: break

        @wraps(self.mthd, assigned=('__name__', '__module__'))
        def f(*args, **kwargs):
            return self.mthd(*args, **kwargs)

        return self.use_parent_doc(f, overridden)

    def use_parent_doc(self, func, source):
        if source is None:
            raise NameError("Can't find '%s' in parents" % self.name)
        func.__doc__ = source.__doc__
        return func


def ensure_json_serializable(test_dict):
    # Validate that all aruguments are of approved types, coerce if it's easy, else exception
    # TODO: ensure in-place iteration like this is okay
    for key in test_dict:
        if isinstance(test_dict[key], (list, tuple, str, int, float, bool)):
            # No problem to encode json
            continue

        elif test_dict[key] is None:
            continue

        elif isinstance(test_dict[key], (np.ndarray, pd.Index)):
            #TODO: Evaluate risk of precision loss in this call and weigh options for performance
            test_dict[key] = test_dict[key].tolist()

        elif isinstance(test_dict[key], dict):
            test_dict[key] = ensure_json_serializable(test_dict[key])

        else:
            try:
                # In Python 2, unicode and long should still be valid.
                # This will break in Python 3 and throw the exception instead.
                if isinstance(test_dict[key], (long, unicode)):
                    # No problem to encode json
                    continue
            except:
                raise TypeError(key + ' is type ' + type(test_dict[key]).__name__ + ' which cannot be serialized.')

    return test_dict

def is_valid_partition_object(partition_object):
    """Convenience method for determing whether a given partition object is a valid weighted partition of the real number line.
    """
    if (partition_object is None) or ("partition" not in partition_object) or ("weights" not in partition_object):
        return False
    if (len(partition_object['partition']) != (len(partition_object['weights']) + 1)):
        if (len(partition_object['partition']) != len(partition_object['weights'])):
            return False
    # TODO: Evaluate desired tolerance for weights
    if (abs(np.sum(partition_object['weights']) - 1) > 1e-6):
        return False
    return True

def is_valid_categorical_partition_object(partition_object):
    return is_valid_partition_object(partition_object) and (len(partition_object['partition']) != len(partition_object['weights']))

def is_valid_continuous_partition_object(partition_object):
    return is_valid_partition_object(partition_object) and (len(partition_object['partition']) != (len(partition_object['weights']) + 1))


def categorical_partition_data(data):
    """Convenience method for creating weights from categorical data.
    Args:
        data (list-like): The data from which to construct the estimate.
    Returns:
        dict:
            {
                "partition": (list) The categorical values present in the data
                "weights": (list) The weights of the values in the partition.
            }
    """
    s = pd.Series(data).value_counts()
    return {
        "partition": s.index,
        "weights":  s.values / (1. * len(data))
    }

def kde_smooth_data(data):
    """Convenience method for building a partition and weights using a gaussian Kernel Density Estimate and default bandwidth.
    Args:
        data (list-like): The data from which to construct the estimate.
    Returns:
        dict:
            {
                "partition": (list) The edges of the partial partition of reals implied by the data and covariance_factor,
                "weights": (list) The densities of the bins implied by the partition.
            }
    """
    kde = stats.kde.gaussian_kde(data)
    evaluation_partition = np.linspace(start = np.min(data) - (kde.covariance_factor() / 2),
                            stop = np.max(data) + (kde.covariance_factor() / 2),
                            num = np.floor(((np.max(data) - np.min(data)) / kde.covariance_factor()) + 1 ).astype(int))
    cdf_vals = [kde.integrate_box_1d(-np.inf, x) for x in evaluation_partition]
    evaluation_weights = np.diff(cdf_vals)
    #evaluation_weights = [cdf_vals[k+1] - cdf_vals[k] for k in range(len(evaluation_partition)-1)]

    # We need to account for weight outside the explicit partition at this point since we have smoothed.
    # Following is basically a crude rule of thumb for what should be -inf and inf as real endpoints.
    lower_bound = np.min(data) - (1.5 * kde.covariance_factor())
    upper_bound = np.max(data) + (1.5 * kde.covariance_factor())
    partition = [ -np.inf, lower_bound ] + evaluation_partition.tolist() + [ upper_bound, np.inf ]
    weights = [ 0, cdf_vals[0] ] + evaluation_weights.tolist() + [1 - cdf_vals[-1], 0]
    return {
        "partition": partition,
        "weights": weights
    }

def partition_data(data, bins='auto', n_bins=10):
    warnings.warn("partition_data is deprecated and will be removed. Use either continuous_partition_data or \
                    categorical_partition_data instead.", DeprecationWarning)
    return continuous_partition_data(data, bins, n_bins)


def continuous_partition_data(data, bins='auto', n_bins=10):
    """Convenience method for building a partition and weights using simple options.
    Args:
        data (list-like): The data from which to construct the estimate.
        bins (string): One of 'uniform' (for uniformly spaced bins), 'ntile' (for percentile-spaced bins), or 'auto' (for automatically spaced bins)
        n_bins (int): Ignored if bins is auto.
    Returns:
        dict:
            {
                "partition": (list) The endpoints of the partial partition of reals,
                "weights": (list) The densities of the bins implied by the partition.
            }
    """
    if bins == 'uniform':
        bins = np.linspace(start=np.min(data), stop=np.max(data), num = n_bins+1)
    elif bins =='ntile':
        bins = np.percentile(data, np.linspace(start=0, stop=100, num = n_bins+1))
    elif bins != 'auto':
        raise ValueError("Invalid parameter for bins argument")

    hist, bin_edges = np.histogram(data, bins, density=False)

    bin_edges = np.insert(bin_edges, 0, -np.inf)
    bin_edges = np.insert(bin_edges, len(bin_edges), np.inf)
    hist = np.insert(hist, 0, 0)
    hist = np.insert(hist, len(hist), 0)

    return {
        "partition": bin_edges,
        "weights": hist / (1.*len(data))
    }

def remove_empty_intervals(partition_object):
    partition_object['weights'] = np.array(partition_object['weights'])
    partition_object['partition'] = np.array(partition_object['partition'])
    for k in range(len(partition_object['weights'])):
        if (partition_object['weights'][k] == 0):

            #del(partition_object['weights'][k])
            partition_object['weights'] = np.delete(partition_object['weights'],k)
            if ( (k + 1) < len(partition_object['weights'])):
                interval = partition_object['partition'][k+1] - partition_object['partition'][k]
                partition_object['partition'][k+1] = partition_object['partition'][k+1] - (interval / 2)
            #del(partition_object['partition'][k])
            partition_object['partition'] =np.delete(partition_object['partition'],k)
            return remove_empty_intervals(partition_object)
    return partition_object
