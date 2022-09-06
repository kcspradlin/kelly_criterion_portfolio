#!/usr/bin/python3
#
#  file_input_output.py
#  
#  Copyright 2022 Kevin Spradlin, Jr.
#  
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#  
#  Note: The information produced by this program is for informational
#        purposes only.  I make no representations as to the 
#        appropriateness, suitability, or accuracy of its algorithms or
#        output.  I will not be liable for any losses, injuries, or
#        damages arising from its use.  The algorithms used in this
#        program were based on my own views and opinions, so the
#        program's output should not be considered professional
#        financial investment advice.  The output should never be used
#        without first conducting your own research and assessing your
#        own financial situation.
#  

from typing import Dict, List
import os
import time
import sqlite3
import numpy as np
from scipy import stats, optimize
import database_input_output



def decode_lh_parameters_students_t(parameters: np.ndarray, num_dimensions: int) -> Dict:
  """
  This function will convert the elements of the parameters array into a
   location/mean vector, a shape matrix, and degrees of freedom.  It will
   return them as values in a dictionary.

  Created on August 30 and September 5, 2022
  """

  mean_vector: np.ndarray = parameters[0:num_dimensions]

  shape_matrix: np.ndarray = np.zeros((num_dimensions, num_dimensions), dtype=np.float32)

  addend: int = num_dimensions
  for current_column in range(num_dimensions):
    addend -= current_column

    for current_row1 in range(0, current_column):
      shape_matrix[current_row1, current_column] = shape_matrix[current_column, current_row1]

    for current_row2 in range(current_column, num_dimensions):
      shape_matrix[current_row2, current_column] = \
        parameters[current_row2 + current_column * num_dimensions + addend]

  d_f: float = parameters[-1]


  return {'mean_vector': mean_vector, 'shape_matrix': shape_matrix, 'degrees_freedom': d_f}



def generate_simulated_asset_returns(distribution: str, parameters: Dict) -> np.ndarray:
  """
  This function will simulate one period of asset returns using a specific
   model and its parameters.

  Created on September 3, 2022
  """

  if distribution == "Normal":
    return stats.multivariate_normal.rvs(mean=parameters['mean_returns'], 
                                         cov=parameters['covariance_matrix'],
                                         size=1)

  elif distribution == "Student's t":
    return stats.multivariate_t.rvs(loc=parameters['mean_returns'],
                                    shape=parameters['shape_matrix'],
                                    df=parameters['degrees_freedom'],
                                    size=1)

  else:
    return np.zeros(1, dtype=np.float32)



def get_type_simulation_returns(portfolio_db: sqlite3.Connection) -> Dict:
  """
  This function will ask the user to select a distribution to use to simulate asset returns.
   It will check that the asset returns have already been imported into the database.  Lastly,
   the function will calculate the parameters needed to calculate the simulated returns.

  The function will return a dictionary with three keys.
  * 'any_errors', will be True if there are any problems and False if not.
  * 'message', will describe the problem, if there are any, or blank if
    there aren't any.
  * 'distribution', will be a string describing the distribution that will
    be used to calculate the simulated returns.
  * 'parameters', which will contain a dictionary of the parameters that will
    be used to calculate the simulated returns.

  Created on August 15, September 3-
  """

  # first have the user select the type of distribution to use to simulate the returns
  simulation_dist: str = ''
  dist_options: Dict = {'1': "Normal", '2': "Student's t"}

  while not simulation_dist:
    os.system('clear')

    for item_number, item_description in dist_options.items():
      print(f"{item_number:s}: {item_description:s}")


    user_input = input("\nSelect the number of a distribution, or press Enter to exit: ")

    if not user_input:
      print("\nBye\n")
      return {'any_errors': True, 'message': 'Returning to main menu'}

    if user_input not in dist_options:
      print("\nYou must select one of the options or just press Enter")
      user_input = ''
      time.sleep(3)
    else:
      simulation_dist = dist_options[user_input]


  # next check that the asset returns have been already been imported, and if so, 
  #  calculate the parameters needed to simulate the asset returns
  function_results: Dict = {}

  if simulation_dist == "Normal":
    function_results: Dict = setup_normal_distribution_parameters(portfolio_db)

  elif simulation_dist == "Student's t":
    # need to convert asset returns to log returns, then calculate their
    #  mean returns and covariance matrix.
    function_results: Dict = setup_students_t_distribution_parameters(portfolio_db)




  return {'any_errors': function_results['any_errors'], 
          'message': function_results['message'], 
          'distribution': simulation_dist, 
          'parameters': function_results['parameters']}



def is_matrix_pos_semidef(test_matrix: np.array) -> Dict:
  """
  This function will test the array test_matrix to see if it's positive 
   semi-definite, using this definition:

   "A positive semidefinite matrix is a Hermitian matrix all of whose eigenvalues are nonnegative."
   https://mathworld.wolfram.com/HermitianMatrix.html

   It will check if the matrix is square, Hermitian, and only has positive 
   eigenvalues.

   The function will return a dictionary.  One key is 'pass_test', which
   will be True if it's positive semi-definite and False if not.  The
   other key is 'message' will will state why the matrix failed the test,
   or will be blank it it passed the test.

  Created on June 8, 2022
  """

  pass_test: bool = False
  message: str = ''


  # check if the matrix is square
  matrix_dimensions: List = list(test_matrix.shape)

  if len(matrix_dimensions) != 2:
    message = 'Matrix needs to have 2 dimensions'
    return {'pass_test': pass_test, 'message': message}

  if matrix_dimensions[0] != matrix_dimensions[1]:
    message = 'Matrix needs to be square'
    return {'pass_test': pass_test, 'message': message}


  # check if the matrix is Hermitian
  complex_conjugate: np.array = np.matrix.getH(test_matrix)

  if not np.array_equal(test_matrix, complex_conjugate):
    message = "Matrix isn\'t Hermitian - equal to complex conjugate of itself"
    return {'pass_test': pass_test, 'message': message}


  # calculate the matrix's eigenvalues and check if any are negative
  for current_eigenvalue in np.linalg.eigvals(test_matrix):
    if current_eigenvalue < 0:
      message = f"Matrix has eigenvalue of {current_eigenvalue:6.4f}"
      break


  if message:
    return {'pass_test': pass_test, 'message': message}
  else:
    return {'pass_test': True, 'message': ''}



def log_likelihood_multivariate_students_t(parameters: np.ndarray, num_dimensions: int, 
                                           variates: np.ndarray) -> float:
    """
    Returns the negative of the log-likelihood function.  The scipy.optimize module only
     has a 'minimize' function, so you need to use it to minimize the negative of the
     log-likelihood function, which will maximize the positive of the log-likelihood
     function.

    Expect parameters[0:dimension] to be the location vector, parameters[dimension:-1] are the
     elements of the lower triangle of the shape matrix, and parameters[-1] is the degrees of
     freedom.

    Created on August 31 and September 3, 2022
    """

    function_results: Dict = decode_lh_parameters_students_t(parameters, num_dimensions)

    mean_vector: np.ndarray = function_results['mean_vector']

    shape_matrix: np.ndarray = function_results['shape_matrix']

    degrees_freedom: float = float(function_results['degrees_freedom'])


    # need to ensure that the shape matrix is positive definite or semi-definite
    # first, test it.  if it passes the test, then calculate the likelihood function
    # if it fails the test, calculate an adjusted shape matrix that passes the
    #  test and use it to calculate the likelihood function
    function_results: Dict = is_matrix_pos_semidef(shape_matrix)

    if not function_results['pass_test']:
        other_function_results: Dict = trial_pos_semidef_matrix(shape_matrix)

        if other_function_results['any_errors']:
            print(other_function_results['message'])
            return 0.0

        shape_matrix = other_function_results['adjusted_matrix']


    temp_sum: float = -np.sum(stats.multivariate_t.logpdf(variates, 
                                                          loc=mean_vector, 
                                                          shape=shape_matrix, 
                                                          df=degrees_freedom))

    return temp_sum



def setup_normal_distribution_parameters(portfolio_db: sqlite3.Connection) -> Dict:
  """
  This function will check if the 'mean_returns' and 'return_covariance_matrix' matrices
    have been calculated or imported.  If so, it will get their data in numpy arrays
    and return them to the calling function, along with some other data.

  This function will return a dictionary with three keys:
  * 'any_errors', will be False if there are any problems or True if there are any
  * 'message', will be blank if there aren't any problems or will be a description
     of the problem if there is one
  * 'sim_parameters' will a dictionary that will contain the mean returns array, the
    covariance matrix array, and the number of assets.

  Created on August 17, 2022
  """

  any_errors: bool = False
  message: str = ''
  sim_parameters: Dict = {}


  # first get the mean returns
  mean_returns: np.ndarray = database_input_output.get_mean_returns(portfolio_db)
  if mean_returns.shape[0] == 1:
    any_errors = True
    message = "Need to import mean returns."


  # next get and check the covariance matrix
  if not any_errors:
    sim_parameters['mean_returns'] = mean_returns.flatten()

    covariance_matrix: np.ndarray = database_input_output.get_covariance_matrix(portfolio_db)
    if covariance_matrix.shape[0] == 1:
      any_errors = True
      message = "Need to import covariance matrix."

  # lastly, check if the covariance matrix is positive semi-definite.  the
  #  'np.random.multivariate_normal' function needs this to be the case.
  if not any_errors:
    sim_parameters['covariance_matrix'] = covariance_matrix

    function_return: Dict = is_matrix_pos_semidef(covariance_matrix)
    if not function_return['pass_test']:
      any_errors = True
      message = f"The covariance matrix needs to be positive semi-definite to run the simulations.  {function_return['message']:s}"

    else:
      sim_parameters['number_of_assets'] = covariance_matrix.shape[0]


  return {'any_errors': any_errors, 'message': message, 'parameters': sim_parameters}



def setup_students_t_distribution_parameters(portfolio_db: sqlite3.Connection) -> Dict:
  """
  This function will check if the asset returns have been imported.  If so, it will place
    them in a numpy array.  Then, the function will use maximum likelihood estimation
    to find the parameters of a multivariate Student's t distribution that fits the
    return data.  The function will then return the parameters to the calling function,
    along with some other data.

  This function will return a dictionary with three keys:
  * 'any_errors', will be False if there are any problems or True if there are any
  * 'message', will be blank if there aren't any problems or will be a description
     of the problem if there is one
  * 'sim_parameters' will a dictionary that will contain the mean returns array, the
    shape matrix array, the degrees of freedom, and the number of assets.

  Created on September 3-5, 2022
  """

  any_errors: bool = False
  message: str = ''
  sim_parameters: Dict = {}


  # first get the return data
  asset_returns: np.ndarray = database_input_output.get_asset_returns(portfolio_db)
  if asset_returns.shape[0] == 1:
    any_errors = True
    message = "Need to import asset returns."


  # next calculate the parameters of the multivariate Student's t distribution
  if not any_errors:
    num_dimensions: int = asset_returns.shape[1]

    # first set up the array with the parameters used in the optimization
    #  function
    init_parameters: np.ndarray = setup_students_t_mle_parameters(num_dimensions, asset_returns)


    # next, set up some boundary conditions for the optimization
    boundary_cond: List = []

    for index, value in enumerate(init_parameters):
      if index < num_dimensions:
        boundary_cond.append([None,None])
      else:
        if value == 1:
          boundary_cond.append([0,100000])
        else:
          boundary_cond.append([None,None])

    boundary_cond[-1] = [1,100000]

    num_elements: int = len(init_parameters)


    # now, run the optimization function
    opt_results = optimize.minimize(log_likelihood_multivariate_students_t, 
                                    x0=init_parameters, 
                                    args=(num_dimensions, asset_returns, ), 
                                    method='Nelder-Mead', bounds=boundary_cond,
                                    options={'maxiter': num_elements * 2000,
                                             'maxfev': num_elements * 2000})


    function_results: Dict = \
      decode_lh_parameters_students_t(opt_results['x'], num_dimensions)      

    #print(f"Estimated mean vector: {np.array2string(function_results['mean_vector'], precision=4):s}")
    #print(f"Estimated covariance matrix: {np.array2string(function_results['shape_matrix'], precision=4):s}")
    #print(f"Estimated degrees of freedom: {function_results['degrees_freedom']:6.2f}")
    #print(opt_results['message'])

    sim_parameters['mean_returns'] = function_results['mean_vector']
    sim_parameters['shape_matrix'] = function_results['shape_matrix']
    sim_parameters['degrees_freedom'] = function_results['degrees_freedom']
    sim_parameters['number_of_assets'] = function_results['shape_matrix'].shape[0]


  return {'any_errors': any_errors, 'message': message, 'parameters': sim_parameters}



def setup_students_t_mle_parameters(num_dimensions: int, asset_returns: np.ndarray) -> np.ndarray:
  """
  This function will set up the array that holds the parameters for the
   optimization function that's used to find the multivariate Student's t
   distribution's parameters.  The array will store information on (1)
   the mean vector, (2) the shape matrix, and (3) the degrees of freedom.

  Created on September 3-5, 2022
  """

  num_elements: int = int(num_dimensions * (num_dimensions + 3) / 2) + 1

  #print(f"Number of dimensions: {num_dimensions:d}")
  #print(f"Number of parameters in optimization problem: {num_elements:d}")


  init_parameters: np.ndarray = np.zeros(num_elements, dtype=np.float32)

  # set the starting values for the mean vector equal to the sample means.
  sample_stats = stats.describe(asset_returns)

  for current_element in range(num_dimensions):
    init_parameters[current_element] = sample_stats[2][current_element]

  # now set the starting values for the covariance matrix.  set the diagonal
  #  elements equal to the same variances.
  current_element:int = num_dimensions
  for step_size in range(num_dimensions, 0, -1):
    if current_element < num_elements:
      init_parameters[current_element] = sample_stats[3][num_dimensions - step_size]
      current_element += step_size

  # finally set the starting value for degrees of freedom equal to the
  #  number of dimensions
  init_parameters[-1] = float(num_dimensions)


  #print(np.array2string(init_parameters, precision=4))


  return init_parameters



def trial_pos_semidef_matrix(test_matrix: np.array) -> Dict:
    """
    This function will take a matrix return a new matrix, based on the
     eigendecomposition of the original matrix.  The original matrix's 
     eigenvalues and vectors will be calculated.  If any eigenvalues are
     non-positive, then they will be set to be slightly positive.  The
     new matrix will be calculated from the original matrix's eigenvectors,
     any of the original eigenvalues that are positive, and the adjusted, 
     now-slightly positive eigenvalues.

    The new matrix will be positive semi-definite.

    Got information about eigendecomposition from this site:
    https://mathworld.wolfram.com/EigenDecomposition.html

    Created on September 3, 2022
    """    

    message: str = ''


    # first, make sure the matrix is symmetric
    matrix_dimensions: List = list(test_matrix.shape)

    if len(matrix_dimensions) != 2:
        message = 'Matrix needs to have 2 dimensions'
        return {'any_errors': True, 'message': message}

    if matrix_dimensions[0] != matrix_dimensions[1]:
        message = 'Matrix needs to be square'
        return {'any_errors': True, 'message': message}


    if not np.array_equal(test_matrix, test_matrix.T):
        message = "Matrix isn\'t symmetric"
        return {'any_errors': True, 'message': message}


    # next, calculate the eigenvalues and eigenvectors of the matrix
    matrix_p: np.ndarray = np.zeros((matrix_dimensions[0], matrix_dimensions[0]), dtype=np.float32)
    matrix_d: np.ndarray = np.zeros((matrix_dimensions[0], matrix_dimensions[0]), dtype=np.float32)

    test_eigenvalues, test_eigenvectors = np.linalg.eig(test_matrix)


    for current_index, current_eigenvalue in enumerate(test_eigenvalues):
        matrix_p[:,current_index] = test_eigenvectors[:,current_index]

        if current_eigenvalue >= 0.0:
            matrix_d[current_index, current_index] = current_eigenvalue
        else:
            matrix_d[current_index, current_index] = np.random.rand() / 10.0


    adjusted_matrix: np.ndarray = np.matmul(matrix_p, matrix_d)
    adjusted_matrix = np.matmul(adjusted_matrix, np.linalg.inv(matrix_p))


    #print(f"Eigenvalues: {np.array2string(test_eigenvalues, precision=4):s}")
    #print(f"Eigenvectors: {np.array2string(test_eigenvectors, precision=4):s}")

    #print(f"Eigenvector matrix: {np.array2string(matrix_p, precision=4):s}")
    #print(f"Eigenvalue matrix: {np.array2string(matrix_d, precision=4):s}")
    #print(f"Test matrix: {np.array2string(test_matrix, precision=4):s}")
    #print(f"Adjusted matrix: {np.array2string(adjusted_matrix, precision=4):s}")


    return {'any_errors': False, 'message': '', 'adjusted_matrix': adjusted_matrix}
