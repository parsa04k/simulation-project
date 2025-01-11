'''
this file calculates  times between events by its given parameters
'''

import random
from math import log, sqrt, cos, pi

class Arrival_rate:
    EMERGENCY_RATE = 15
    NORMAL_RATE = 60
    
class Tri_parameters:
    MIN = 5
    PEAK = 75
    MAX = 100
    
class Simple_Surgery_parameters:
    MEAN = 30.22
    STD = 4.95
    
class Moderate_Surgery_parameters:
    MEAN = 74.54
    STD = 9.95
    
class Complex_Surgery_parameters:
    MEAN = 244.26
    STD = 59.4
    
class Icu_and_ccu_stay_parameters:
    LAMBDA = 1500 # 25 hours
    
class Ward_stay_time:
    LAMBDA = 3000 # 50 hours
    
def exponential(rate):
    random_number = random.uniform(0,1)
    time = -(rate)*log(1-random_number)
    return time

def triangular_distribution_time():
    """
    Generate random samples from a triangular distribution.
    """
    random_number = random.uniform(0,1)
    F_peak = ((Tri_parameters.PEAK - Tri_parameters.MIN)/(Tri_parameters.MAX - Tri_parameters.MIN)) # (c-a)/(b-a)
    if random_number <= F_peak:
        time = sqrt(random_number*(Tri_parameters.MAX - Tri_parameters.MIN)*(Tri_parameters.PEAK - Tri_parameters.MIN)) + Tri_parameters.MIN
        #  time = sqrt(F(x)*(b-a)*(c-a)) + a
    else:
        time = Tri_parameters.MAX - sqrt((1-random_number)*(Tri_parameters.MAX - Tri_parameters.MIN)*(Tri_parameters.PEAK - Tri_parameters.MIN))
        #  time = b - sqqrt( (1-F(x)) * (b-a) * (c-a))
    return time

def box_muller():
    """ Generate a random number following a normal distribution using the Box-Muller transform.
    Returns: float: A random number following a normal distribution. 
    """ 
    u1 = random.uniform(0,1)
    u2 = random.uniform(0,1) 
    z0 = sqrt(-2.0 * log(u1)) * cos(2.0 * pi * u2) 
    return z0 if abs(z0)<=6 else (z0/abs(z0))*6

def simple_surgery_time():
    time = Simple_Surgery_parameters.MEAN + box_muller()*Simple_Surgery_parameters.STD
    return time

def moderate_surgery_time():
    time = Moderate_Surgery_parameters.MEAN + box_muller()*Moderate_Surgery_parameters.STD
    return time
    
def complex_surgery_time():
    time = Complex_Surgery_parameters.MEAN + box_muller()*Moderate_Surgery_parameters.STD
    return time

