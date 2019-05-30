"""
Test script for the hierarchical classes.
"""

import os
import pytest
import numpy as np
from cwinpy.hierarchical import (BaseDistribution,
                                 BoundedGaussianDistribution,
                                 ExponentialDistribution,
                                 MassQuadrupoleDistribution,
                                 create_distribution)
from bilby.core.prior import Uniform
from bilby.core.result import (Result, ResultList)


class TestDistributionObjects(object):
    """
    Tests for the distribution objects.
    """

    def test_base_distribution(self):
        """
        Test the BaseDistribution object.
        """

        name = 'test'

        # test failure for unknown distribution
        with pytest.raises(ValueError):
            BaseDistribution(name, 'kjsgdkdgkjgsda')
        
        # test failure for inappropriate bounds
        with pytest.raises(ValueError):
            BaseDistribution(name, 'gaussian', low=0., high=-1.)

        # test failure for unknown hyperparameter name
        with pytest.raises(KeyError):
            hyper = {'mu': [1], 'dkgwkufd': [2]}
            BaseDistribution(name, 'gaussian', hyperparameters=hyper)

        # test failure with invalid hyperparameter type
        with pytest.raises(TypeError):
            BaseDistribution(name, 'gaussian', hyperparameters='blah')
        
        with pytest.raises(TypeError):
            hyper = 'blah'
            BaseDistribution(name, 'exponential', hyperparameters=hyper)

        # test default log_pdf is NaN
        hyper = {'mu': 2.}
        dist = BaseDistribution(name, 'exponential',
                                hyperparameters=hyper)

        assert dist['mu'] == hyper['mu']
        assert np.isnan(dist.log_pdf({}, 0))
        assert dist.sample({}) is None

        # test failure when getting unknown item
        with pytest.raises(KeyError):
            val = dist['kgksda']

        del dist

        # test setter failure
        dist = BaseDistribution(name, 'exponential')

        with pytest.raises(KeyError):
            dist['madbks'] = Uniform(0., 1., 'mu')

        # test setter
        dist['mu'] = Uniform(0., 1., 'mu')
        assert isinstance(dist['mu'], Uniform)

    def test_bounded_gaussian(self):
        """
        Test the BoundedGaussianDistribution class.
        """

        name = 'test'

        # test failures
        with pytest.raises(TypeError):
            BoundedGaussianDistribution(name, mus='blah')

        with pytest.raises(TypeError):
            BoundedGaussianDistribution(name, mus=[1], sigmas='blah')

        with pytest.raises(TypeError):
            BoundedGaussianDistribution(name, mus=[1], sigmas=[1],
                                        weights='blah')

        with pytest.raises(ValueError):
            BoundedGaussianDistribution(name, mus=[1.], sigmas=[1., 2.])

        with pytest.raises(ValueError):
            BoundedGaussianDistribution(name, mus=[1., 2.], sigmas=[1., 2.],
                                        weights=[1])

        with pytest.raises(ValueError):
            BoundedGaussianDistribution(name)

        dist = BoundedGaussianDistribution(name, mus=[1., 2.], sigmas=[1., 2.])

        assert dist.nmodes == 2
        assert np.all(np.array(dist['weight']) == 1.)

        del dist
        # test log pdf
        dist = BoundedGaussianDistribution(name, mus=[Uniform(0., 1., 'mu0'), 2.],
                                           sigmas=[Uniform(0., 1., 'sigma0'), 2.],
                                           weights=[Uniform(0., 1., 'weight0'), 2.])

        value = 1.
        hyper = {'mu8': 0.5, 'sigma0': 0.5, 'weight0': 0.5}
        with pytest.raises(KeyError):
            dist.log_pdf(hyper, value)

        hyper = {'mu0': 0.5, 'sigma8': 0.5, 'weight0': 0.5}
        with pytest.raises(KeyError):
            dist.log_pdf(hyper, value)

        hyper = {'mu0': 0.5, 'sigma0': 0.5, 'weight8': 0.5}
        with pytest.raises(KeyError):
            dist.log_pdf(hyper, value)

        hyper = {'mu0': 0.5, 'sigma0': 0.5, 'weight0': 0.5}
        assert np.isfinite(dist.log_pdf(hyper, value))

        # check negative values give -inf by default
        value = -1.
        assert dist.log_pdf(hyper, value) == -np.inf

        # check drawn sample is within bounds
        assert dist.low < dist.sample(hyper) < dist.high

    def test_exponential(self):
        """
        Test the ExponentialDistribution class.
        """

        name = 'test'

        with pytest.raises(TypeError):
            ExponentialDistribution(name, mu=1.)

        dist = ExponentialDistribution(name, mu=Uniform(0., 1., 'mu'))

        value = -1.
        hyper = {'mu': 0.5}
        assert dist.log_pdf(hyper, value) == -np.inf

        # check drawn sample is within bounds
        assert dist.low < dist.sample(hyper) < dist.high

        value = 1.
        hyper = {'kgsdg': 0.5}
        with pytest.raises(KeyError):
            dist.log_pdf(hyper, value)

    def test_create_distribution(self):
        """
        Test the create_distribution() function.
        """

        name = 'test'
        with pytest.raises(ValueError):
            create_distribution(name, 'kjbskdvakvkd')
        
        with pytest.raises(TypeError):
            create_distribution(name, 2.3)

        gausskwargs = {'mus': [1., 2.], 'sigmas': [1., 2.]}
        dist = create_distribution(name, 'Gaussian', gausskwargs)

        assert isinstance(dist, BoundedGaussianDistribution)
        assert (dist['mu0'] == gausskwargs['mus'][0] and
                dist['mu1'] == gausskwargs['mus'][1])
        assert (dist['sigma0'] == gausskwargs['sigmas'][0] and
                dist['sigma1'] == gausskwargs['sigmas'][1])
        del dist
        
        expkwargs = {'mu': Uniform(0., 1., 'mu')}
        dist = create_distribution(name, 'Exponential', expkwargs)
        assert isinstance(dist, ExponentialDistribution)
        assert dist['mu'] == expkwargs['mu']

        newdist = create_distribution(name, dist)
        assert isinstance(newdist, ExponentialDistribution)
        assert newdist['mu'] == dist['mu']


class TestMassQuadrupoleDistribution(object):
    """
    Test the MassQuadrupoleDistribution object.
    """

    def test_mass_quadrupole_distribution(self):
        # test data sets from bilby
        testdata1 = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'data', 'hierarchical_test_set_0_result.json')
        testdata2 = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'data', 'hierarchical_test_set_1_result.json')

        # test invalid q22range (lower bounds is less than upper bound)
        with pytest.raises(ValueError):
            MassQuadrupoleDistribution(q22range=[100., 1.])

        # test invalid q22range (only one value passed)
        with pytest.raises(ValueError):
            MassQuadrupoleDistribution(q22range=[100.])

        # test invalid data type
        with pytest.raises(TypeError):
            MassQuadrupoleDistribution(data=1)

        res = ResultList([testdata1, testdata2])

        # remove Q22 from results to test error
        del res[0].posterior['Q22']
        with pytest.raises(RuntimeError):
            MassQuadrupoleDistribution(data=res)

        # distribution with wrong name (i.e., not 'Q22')
        pdist = ExponentialDistribution('Blah', mu=Uniform(0., 1e37, 'mu'))
        with pytest.raises(ValueError):
            MassQuadrupoleDistribution(data=[testdata1, testdata2],
                                       distribution=pdist)

        # distribution with no priors to infer
        pdist = BoundedGaussianDistribution('Q22', mus=[0.], sigmas=[1e34])
        with pytest.raises(ValueError):
            MassQuadrupoleDistribution(data=[testdata1, testdata2],
                                       distribution=pdist)

        # unknown sampler type
        pdist = ExponentialDistribution('Q22', mu=Uniform(0., 1e32, 'mu'))
        with pytest.raises(ValueError):
            MassQuadrupoleDistribution(data=[testdata1, testdata2],
                                       distribution=pdist, sampler='akgkfsfd')

        # unknown bandwidth type for KDE
        bw = 'lkgadkgds'
        with pytest.raises(RuntimeError):
            MassQuadrupoleDistribution(data=[testdata1, testdata2],
                                       distribution=pdist, bw=bw)

        # test sampler
        mdist = MassQuadrupoleDistribution(data=[testdata1, testdata2],
                                           distribution=pdist)
        res = mdist.sample(**{'Nlive': 100, 'save': False})

        assert isinstance(res, Result)

        del res
        del mdist

        # test grid sampler
        grid = {'mu': 100, 'Q22': 100}
        mdist = MassQuadrupoleDistribution(data=[testdata1, testdata2],
                                           distribution=pdist,
                                           grid=grid)
