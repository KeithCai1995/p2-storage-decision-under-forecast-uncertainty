from __future__ import annotations
import sys
import unittest
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storage_decision.battery import empirical_cvar_loss

class TestEmpiricalCVaR(unittest.TestCase):
    def test_integer_tail_mass(self):
        self.assertAlmostEqual(empirical_cvar_loss(-np.arange(10.0),0.8),8.5,places=12)
    def test_fractional_boundary_mass(self):
        self.assertAlmostEqual(empirical_cvar_loss(-np.array([0.,1.,2.,3.]),0.6),2.625,places=12)
    def test_ties_do_not_expand_the_tail(self):
        self.assertAlmostEqual(empirical_cvar_loss(-np.array([0.,5.,5.,5.,10.]),0.6),7.5,places=12)
    def test_near_tie_perturbation_is_continuous(self):
        losses=np.array([0.,0.,0.,0.,0.,5.,5.,5.,5.,10.])
        baseline=empirical_cvar_loss(-losses,0.7)
        for direction in (-1.,1.):
            changed=losses.copy();changed[6]+=direction*1e-12
            value=empirical_cvar_loss(-changed,0.7)
            self.assertLessEqual(abs(value-baseline),1e-12)
            self.assertEqual(value,empirical_cvar_loss(-changed[::-1],0.7))
    def test_less_than_one_observation_in_tail(self):
        self.assertAlmostEqual(empirical_cvar_loss(-np.array([-3.,2.,7.]),0.99),7.,places=12)
    def test_zero_alpha_and_constant_or_negative_losses(self):
        self.assertAlmostEqual(empirical_cvar_loss(np.array([1.,2.,6.]),0.),-3.,places=12)
        self.assertAlmostEqual(empirical_cvar_loss(np.full(7,4.),0.9),-4.,places=12)
    def test_matches_independent_rockafellar_uryasev_lp(self):
        for losses,alpha in [(np.array([0.,5.,5.,5.,10.]),0.6),(np.array([0.,1.,2.,3.]),0.6),(np.array([-9.,-5.,-5.,-1.]),0.9),(np.random.default_rng(17).normal(size=60),0.9)]:
            n=len(losses)
            result=linprog(np.r_[1.,np.full(n,1./((1.-alpha)*n))],A_ub=np.column_stack([-np.ones(n),-np.eye(n)]),b_ub=-losses,bounds=[(None,None)]+[(0.,None)]*n,method="highs")
            self.assertTrue(result.success,result.message)
            self.assertAlmostEqual(empirical_cvar_loss(-losses,alpha),result.fun,places=10)
    def test_rejects_invalid_inputs(self):
        for profits in [np.array([]),np.array([[1.]]),np.array([np.nan]),np.array([np.inf])]:
            with self.assertRaises(ValueError):empirical_cvar_loss(profits)
        for alpha in [-0.1,1.,np.nan,np.inf]:
            with self.assertRaises(ValueError):empirical_cvar_loss(np.array([1.]),alpha)
if __name__ == "__main__":
    unittest.main()
