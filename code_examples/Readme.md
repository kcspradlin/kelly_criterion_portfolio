### Readme
#### Last updated on September 5, 2022


I used the Jupyter notebooks in this directory to set up code and
algorithms for estimating parameters of multivariate normal and 
Student's t distributions.  I used a maximum likelihood approach with
asset returns to find the distribution parameters.

The notebooks are set up so that you define distribution means, 
covariance or shape matrices, and degrees of freedom.  A random sample
will be generated from a distribution using your inputs.  Then the 
notebooks will use maximum likelihood estimation to find parameters
that best fit the distribution using the random sample.

I know that the code and algorithms are working correctly by comparing
the estimated parameters with the ones I entered into the notebooks.
The estimates aren't exact matches for the parameters I entered, but 
they're close enough to give me confidence that the approach is working.

The files in this folder (aside from this 'Readme.md' file) are:

* '1_mle_normal_distribution.ipynb': this notebook is based around a 
univariate normal distribution.

* '2_mle_multivariate_normal_distribution.ipynb': this notebook is based
around a multivariate normal distribution.

* '3_mle_multivariate_student_t_distribution.ipynb': this notebook is 
based around a multivariate Student's t distribution.
