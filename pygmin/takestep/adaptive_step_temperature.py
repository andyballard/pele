import numpy as np

class AdaptiveStepsizeTemperature(object):
    """
    todo: 
        make the interface with changing the temperature not quite so ugly
    """
    def __init__(self, stepclass, target_accept_prob = 0.5, interval=50, Tfactor=0.9, 
                 sfactor=0.9, ediff=.001, verbose=True):
        """
        adjust both the stepsize and the temperature adaptively
        
        Parameters
        ----------
        
        stepclass : 
            the step taking class
        target_accept_prob : 
            the target acceptance probability
        interval : 
            the interval at which to adjust temperature and stepsize
        Tfactor : 
            the factor with which to multipy (or divide) the temperature
        sfactor : 
            the factor with which to multipy (or divide) the stepsize
        ediff : 
            if two minima have energies that are within ediff from each other then
            they are considered to be the same minimum
        verbose :
            print status messages
            
        Notes
        -----                    
        We will base the stepsize adjustment on the probability of ending up 
        in a different minimum
        
        We will base the temperature adjustment on the probability of accepting
        a move that ended up in a different minimum
        """
        self.stepclass = stepclass
        self.target_accept_prob = target_accept_prob
        self.interval = interval
        self.Tfactor = Tfactor
        self.sfactor = sfactor
        self.ediff = ediff
        self.verbose = verbose
        
        self.energy = None
        self.coords = None
        
        self.ncalls_tot = 0
        self.reset()
    
    def reset(self):
        self.nattempts = 0
        self.naccept = 0
        self.nsame = 0
        
    
    def takeStep(self, *args, **kwargs):
        """
        basinhopping calls this to take a step
        """
        self.stepclass.takeStep(*args, **kwargs)
    
    def updateStep(self, accepted, driver=None):
        """
        this is the function basinhopping uses to report results
        """
        self.ncalls_tot += 1
        trial_energy = driver.trial_energy
        trial_coords = driver.trial_coords
        if self.energy is None:
            #first time called. Save energy and coords
            self.energy = trial_energy
            self.coords = np.copy(trial_coords)
            return
        
        self.nattempts += 1
        same = False
        if accepted:
            self.naccept += 1
        if abs(self.energy - trial_energy) <= self.ediff:
            #if np.std(self.coords - trial_coords) <= self.xdiff:
            same = True
            self.nsame += 1
        #print abs(self.energy - trial_energy), np.std(self.coords - trial_coords), np.max(np.abs(self.coords - trial_coords))
        if not same:
            self.energy = trial_energy
            self.coords = np.copy(trial_coords)
       
        if self.nattempts % self.interval == 0:
            self.adjustStep()
            self.adjustTemp(driver)
            self.reset()
        
    def adjustStep(self):
        """adjust the step size"""
        fsame = float(self.nsame) / self.nattempts
        if fsame > self.target_accept_prob:
            self.stepclass.scale(1. / self.sfactor)
        else:
            self.stepclass.scale(self.sfactor)
        if self.verbose:
            print "naccept nsame ndiff, naccept_diff %d %d %d %d" % (
                self.naccept, self.nsame, self.nattempts-self.nsame,
                self.naccept-self.nsame)
            print "stepsize is now %.4g ratio %.4g" %(self.stepclass.stepsize,
                                                      fsame)
            
            
    def adjustTemp(self, driver):
        """adjust the temperature"""
        ndiff = self.nattempts - self.nsame
        ndiff_accept = self.naccept - self.nsame
        if ndiff == 0:
            faccept = 1
        else:
            faccept = float(ndiff_accept) / ndiff
        if faccept > self.target_accept_prob:
            driver.acceptTest.temperature *= self.Tfactor
        else:
            driver.acceptTest.temperature /= self.Tfactor
        if self.verbose:
            print "temperature is now %.4g ratio %.4g" %(driver.acceptTest.temperature,
                                                         faccept)

if __name__ == "__main__":
    import numpy as np
    import pygmin.potentials.lj as lj
    import pygmin.basinhopping as bh
    from pygmin.takestep import displace
    #from pygmin.takestep import adaptive
    
    natoms = 38
    
    # random initial coordinates
    coords=np.random.random(3*natoms)
    potential = lj.LJ()
    
    takeStep = displace.RandomDisplacement( stepsize=0.3 )
    tsAdaptive = AdaptiveStepsizeTemperature(takeStep, target_accept_prob=0.5,
                                             interval=100)
    opt = bh.BasinHopping(coords, potential, takeStep=tsAdaptive)
    opt.printfrq = 50
    opt.run(1000)
        