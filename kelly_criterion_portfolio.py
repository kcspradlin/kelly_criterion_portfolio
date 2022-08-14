#!/usr/bin/python3
#
#  kelly_criterion_portfolio.py
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


from typing import Dict, List, IO, Set
import sqlite3
import os
import time
import re
import random
import numpy as np
import quadprog
import tqdm
import file_input_output
import database_input_output



def main():
  """
  Prints a menu to the command line.  The menu lets the user
  * import and view a vector of means and the covariance matrix of the
    excess returns,
  * calculate the optimal portfolio allocations to assets with these
    means and variances/covariances, based on the Kelly Criterion and
    on the assumption that the allocations add up to 1.0.
  * do a Monte Carlo simulation, to determine some statistics of 
    portfolios based on the optimal allocations and on factors of these
    optimal allocations.
  
  Created in June 15-23, 2022
  Modified on July 24, 2022
  * used refactoring tips from:
    https://www.python-engineer.com/posts/python-refactoring-tips/
  """
  # set up a internal database that holds user-provided and 
  #  calculated asset return and portfolio data
  portfolio_db: sqlite3.Connection = sqlite3.connect(":memory:")
  set_up_portfolio_db(portfolio_db)


  # clear screen then print console menu then wait for user input
  console_menu: Dict = set_up_console_menu()
  user_input: str = ''

  while not user_input:
    os.system('clear')

    print("This application will estimate a portfolio's asset")
    print(" allocations and return statistics, based on information")
    print(" provided by the user, in order to maximize the growth")
    print(" rate of the portfolio\'s value.\n")

    for item_number, item_command in console_menu.items():
      print(f"{item_number:s}: {item_command[0]:s}")


    user_input = input("\nSelect a command, or press Enter to exit: ")

    if not user_input:
      print("\nBye\n")
      portfolio_db.close()

      return
    elif user_input not in console_menu:
      print("\nYou must select one of the commands or just press Enter")
      user_input = ''
      time.sleep(3)
    else:
      if console_menu[user_input][1] in globals():
        globals()[console_menu[user_input][1]](portfolio_db)
        user_input = ''
      else:
        print("\nThe function for that command hasn't yet been set up.")
        user_input = ''
        time.sleep(3)


  portfolio_db.close()

  return



def set_up_portfolio_db(portfolio_db: sqlite3.Connection):
  """
  This function will set up tables in the portfolio_db database to 
   hold means and covariances of the assets in the portfoliio and the
   optimal allocations of funds to the assets in the portfolio. 
  If they already exist, then they will first be deleted.

  Created on June 20-22, July 10, and July 25 2022
  """

  db_cursor: sqlite3.Cursor = portfolio_db.cursor()

  check_query: str = \
    "select name from sqlite_master where type = 'table' and name = '{0:s}';"

  drop_query: str = "drop table {0:s};"

  create_queries: Dict = \
    {'mean_returns': "create table mean_returns(asset integer, mean_return real, primary key(asset));",
     'return_covariance_matrix': "create table return_covariance_matrix(asset1 integer, asset2 integer, var_covar real, primary key(asset1, asset2));",
     'filepaths': "create table filepaths(description text, filepath text, primary key(description));",
     'test_portfolios': "create table test_portfolios(portfolio integer, asset integer, allocation real, primary key(portfolio, asset));",
     'asset_returns': "create table asset_returns(time_period integer, asset integer, return real, primary key(asset, time_period));"}

  table_names: Set = set(create_queries.keys())


  # go through each table in the 'tables_names' set.  if it is already in the database, then
  #  delete it and set up a blank one.
  for current_table in table_names:
    db_cursor.execute(check_query.format(current_table))
    table_exists = db_cursor.fetchone()

    if table_exists is not None:
      db_cursor.execute(drop_query.format(current_table))
      portfolio_db.commit()


    db_cursor.execute(create_queries[current_table])
    portfolio_db.commit()


  db_cursor.close()

  return



def set_up_console_menu() -> Dict:
  """
  This function just sets up a dictionary to hold the menu names of the
   functions.

  Created on June 19, 2022
  """

  console_menu: Dict = {}
  console_menu['1'] = ('Import asset return data into internal db', 'import_return_data', )
  console_menu['2'] = ('Calculate asset returns using price data', 'import_price_data', )
  console_menu['3'] = ('Display imported asset return data', 'show_return_data', )
  console_menu['4'] = ('Calculate portfolio allocations', 'calculate_portfolio_allocations', )
  console_menu['5'] = ('Estimate portfolio statistics', 'simulate_portfolio_values', )

  return console_menu



def import_return_data(portfolio_db: sqlite3.Connection):
  """
  This function will ask the user for the directory and name of the file containing 
   the asset return means and covariance matrix, will open the file, will run a couple
   of checks on the data, and if the data's OK will finally import the data into the 
   'portfolio_db' database.

  Created on June 19-20, July 4, and July 10, 2022
  """

  # get the file path of the file with the asset return data
  user_message: str = 'Looking for the file with asset returns and covariances'
  function_results: Dict = file_input_output.get_filename(user_message)
  if function_results['any_errors']:
    print(function_results['message'])
    time.sleep(6)
    return


  asset_return_filepath: str = function_results['filepath']


  # clear out the database.
  set_up_portfolio_db(portfolio_db)


  # open the file.  check that it has the expected format, if it has the
  # format, then import its data and run some checks on it.  if the 
  # data's good, then store it in the database.
  import_results: Dict = get_asset_return_data(asset_return_filepath, portfolio_db)
  if import_results['any_errors']:
    print(f"{import_results['message']:s}")
    time.sleep(6)
    return

  return



def get_asset_return_data(asset_return_filepath: str, portfolio_db: sqlite3.Connection) -> Dict:
  """
  This function will open the file using the 'asset_return_filepath' parameter and
  parse the data in the file.  if it has the expected format and if the data passes
  some checks, then the function will save it to the 'mean_returns' and 
  'return_covariance_matrix' tables in the 'portfolio_db' database.  It will also
  save the file and directory in the 'filepaths' table.
  
  The function will:
  * verify that the mean return and covariance matrix is composed of floating-point
    numbers.
  * verify that the number of mean returns matches the number of rows in the covariance
    matrix and that the covariance matrix is square.
  * verify that the covariance matrix is invertible and is positive semi-definite.  The
    former is needed to find the optimal fs and the latter is needed to run the portfolio
    return simulations.
  
  The function will return a dictionary with two keys.  One, 'any_errors', will be False
  if there are any problems or True if there are.  The second key, 'message', will be
  blank if there aren't any problems or will be a description of the problem if there
  is a problem.
  
  Created on June 19-20 and July 10, 2022   
  """

  # parse the data in the file
  parse_function_results: Dict = file_input_output.parse_asset_return_file(asset_return_filepath)
  if parse_function_results['any_errors']:
    return {'any_errors': True, 'message': parse_function_results['message']}


  # since there aren't any problems with the mean returns and covariance
  #  matrix data, save them to the database.  also, need the covariance
  #  matrix to be in the database in order to put it into a numpy array
  #  and perform the next set of tests.
  database_input_output.import_mean_returns(parse_function_results['mean_returns'], portfolio_db)
  database_input_output.import_covariance_matrix(parse_function_results['covariance_matrix'], portfolio_db)
  database_input_output.import_filepath('asset_returns', asset_return_filepath, portfolio_db)


  # check the covariance matrix.  if it's invertible and positive semi-definite,
  #  then import it into the database.
  covariance_matrix: np.ndarray = database_input_output.get_covariance_matrix(portfolio_db)

  if np.linalg.det(covariance_matrix) == 0:
    print("The covariance matrix isn\'t invertible, so the portfolio allocations can\'t be calculated.")
    print("Try different asset(s) or making small changes to the matrix elements.")
    time.sleep(6)


  function_return: Dict = is_matrix_pos_semidef(covariance_matrix)
  if not function_return['pass_test']:
    print("The covariance matrix needs to be positive semi-definite to run the simulations.")
    print(f"{function_return['message']:s}")
    print("Try different asset(s) or making small changes to the matrix elements.")
    time.sleep(6)


  return {'any_errors': False, 'message': ''}



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



def import_price_data(portfolio_db: sqlite3.Connection):
  """
  This function will ask the user for the directory and name of the file containing 
   the asset prices, will open the file, and run a couple of checks on the data.  If
   the data's OK, the function will calculate asset returns using the price data, and
   will calculate means and a covariance matrix of those returns, and finally import
   the data into the 'portfolio_db' database.

  Created on July 25-31, 2022
  """

  # get the file path of the file with the asset return data
  user_message: str = 'Looking for the file with asset price histories'
  function_results = file_input_output.get_filename(user_message)
  if function_results['any_errors']:
    print(function_results['message'])
    time.sleep(6)
    return


  asset_price_filepath: str = function_results['filepath']


  # clear out the database.
  set_up_portfolio_db(portfolio_db)


  # open the file.  check that it has the expected format, if it has the
  # format, then import its data and run some checks on it.  if the 
  # data's good, then store it in the database.
  parse_function_results: Dict = file_input_output.parse_asset_price_data(asset_price_filepath)
  if parse_function_results['any_errors']:
    print(f"{parse_function_results['message']:s}")
    time.sleep(6)
    return


  # since there aren't any problems with the price return data, save it
  #  to the database, along with the name of the price data file.
  database_input_output.import_asset_returns(parse_function_results['asset_return_data'], 
                                             portfolio_db)
  database_input_output.import_filepath('asset_prices', asset_price_filepath, portfolio_db)


  # now calculate the means and covariances of the asset returns, and then
  # save them to the database
  import_function_results: Dict = \
    database_input_output.import_mean_covariance_matrices(parse_function_results['asset_return_data'], 
                                                          portfolio_db)
  if import_function_results['any_errors']:
    print(f"{import_function_results['message']:s}")
    time.sleep(6)


  return



def show_return_data(portfolio_db: sqlite3.Connection):
  """
  This function will display the asset return means and covariance matrix 
   provided by the user.  It can be used to verify the data that's being used
   by the portfolio construction algorithm.

  Created on June 20, 2022 
  """

  os.system('clear')


  # put the mean return and covariance matrix data into numpy arrays
  mean_returns: np.ndarray = database_input_output.get_mean_returns(portfolio_db)

  covariance_matrix: np.ndarray = database_input_output.get_covariance_matrix(portfolio_db)


  print("Mean returns")
  print(mean_returns)

  print("\nCovariance matrix")
  print(covariance_matrix)


  time.sleep(6)


  return



def calculate_portfolio_allocations(portfolio_db: sqlite3.Connection):
  """
  This function will calculate the portfolio allocations needed to maximize
   the growth rate of the portfolio's value, under the assumptions that
   the assets' rates of growth are joint normally distributed and that
   the total of the allocations add up to 100%.

  Next, it will ask the user if they want to use 11 randomly-created
   portfolios in the simulation or if they want to import some portfolios
  (up to 11) from their own file.  

  Regardless of the choice taken, the function will save these portfolios'
   allocations to the 'test_portfolios' table in the database.
  
  Created on June 20-22, and July 4, 10, and 20, 2022
  """

  # first, calculate the portfolio allocations that maximize the growth rate
  # get the mean return and covariance matrices, if they have been imported.
  mean_returns: np.ndarray = database_input_output.get_mean_returns(portfolio_db)
  if mean_returns.shape[0] == 1:
    print("Need to import mean returns.")
    time.sleep(6)
    return


  covariance_matrix: np.ndarray = database_input_output.get_covariance_matrix(portfolio_db)
  if covariance_matrix.shape[0] == 1:
    print("Need to import covariance matrix.")
    time.sleep(6)
    return


  # determine if the user wants the portfolio to be build only with long
  #  positions, or if both long and short positions are OK
  user_response: str = get_type_portfolio_positions()

  if user_response == 'y':
    long_only_portfolio: bool = True
  elif user_response == 'n':
    long_only_portfolio: bool = False
  else:
    return


  # calculate the optimal portfolio
  function_results: Dict = \
    calculate_optimal_fs(mean_returns, covariance_matrix, long_only_portfolio)
  if function_results['any_errors']:
    print(f"{function_results['message']:s}")
    time.sleep(6)
    return

  optimal_fs: np.ndarray = function_results['optimal_fs']


  # ask the user if they want to use test portfolios provided by them of
  #  if they want the function to generate some random portfolios.
  user_portfolio_allocations: List = []
  computer_portfolio_allocations: List = []


  os.system('clear')

  user_choice: str = \
    input("Do you want to provide portfolio allocations to test?\n (Y for yes or N or Enter key for no) ")


  if user_choice.lower() == 'y':
    # get the file path of the file with the asset return data
    user_message: str = 'Looking for the file with test portfolio allocations'
    function_results = file_input_output.get_filename(user_message)
    if function_results['any_errors']:
      print(function_results['message'])
      time.sleep(6)
      return


    portfolio_allocation_filepath: str = function_results['filepath']

    # get the portfolio allocation date from the file
    import_results: Dict = get_user_portfolio_allocation_data(portfolio_allocation_filepath)
    if import_results['any_errors']:
      print(f"{import_results['message']:s}")
      time.sleep(6)
      return

    user_portfolio_allocations = import_results['allocations']
    database_input_output.import_filepath('user_portfolios', portfolio_allocation_filepath, 
                                          portfolio_db)

  elif user_choice.lower() == 'n' or not user_choice:
    computer_portfolio_allocations = create_random_portfolios(optimal_fs, long_only_portfolio)


  os.system('clear')


  # import the optimal portfolio and the test portfolios to the 'test_portfolios' table
  if user_portfolio_allocations:
    database_input_output.import_test_portfolios(portfolio_db, optimal_fs, 
                                                 user_portfolio_allocations)
  else:
    database_input_output.import_test_portfolios(portfolio_db, optimal_fs, 
                                                 computer_portfolio_allocations)


  # print the portfolio allocations to the screen
  number_of_assets: int = optimal_fs.shape[0]

  if user_portfolio_allocations:
    print("First six user-provided portfolios\n")
    for current_portfolio, current_allocations in enumerate(user_portfolio_allocations):
      if current_portfolio < 6:
        output_string: str = f"{current_portfolio + 1:d}"

        for current_asset in range(number_of_assets):
          output_string += f"\t{current_allocations[current_asset]:8.6f}"

        print(output_string)

  else:
    print("First six randomly-created portfolios\n")
    for current_portfolio, current_allocations in enumerate(computer_portfolio_allocations):
      if current_portfolio < 6:
        output_string: str = f"{current_portfolio:d}"

        for current_asset in range(number_of_assets):
          output_string += f"\t{current_allocations[current_asset]:8.6f}"

        print(output_string)


  print("\nOptimal portfolio allocations\n")
  print(optimal_fs)
  time.sleep(12)

#  print(insert_records)
#  time.sleep(30)

  return



def get_user_portfolio_allocation_data(portfolio_allocation_filepath: str) -> Dict:
  """
  This function will open the file file 'file_name' in the directory 'directory_name' and
  parse the data in the file.  if it has the expected format and if the data passes some 
  checks, then the function will save it to a two-dimensinal list of lists - 
  portfolios in the first element, allocations in the second.
  
  The function will verify that the allocations can be converted to floating-point numbers.
  if there are any missing allocations, the function will return an error message.
  
  The function will return a dictionary with three keys.  One, 'any_errors', will be False
  if there are any problems or True if there are.  The second key, 'message', will be
  blank if there aren't any problems or will be a description of the problem if there
  is a problem.  The third key, 'allocations', will be blank of there are any problems
  or the portfolio allocation list if there aren't any problems.
  
  Created on June 22-23 and July 10, 2022
  """

  portfolio_allocation_file: IO = open(portfolio_allocation_filepath, 'r')


  # copy the portfolio allocation data from the file
  line_from_file: str = portfolio_allocation_file.readline()
  if line_from_file == "number of assets\n":
    number_of_assets_str: str = portfolio_allocation_file.readline()
  else:
    return {'any_errors': True, 'message': "\'number of assets\' not found on first line"}


  for counter in range(2):
    line_from_file = portfolio_allocation_file.readline()


  raw_portfolio_allocations: List = []

  if line_from_file == "portfolio allocations\n":
    while line_from_file:
      line_from_file = portfolio_allocation_file.readline()
      if line_from_file:
        raw_portfolio_allocations.append(line_from_file)

  else:
    return {'any_errors': True, 'message': "\'portfolio allocations\' not found on fourth line"}


  portfolio_allocation_file.close()


  # convert the number of assets to an integer
  if not file_input_output.is_int(number_of_assets_str):
    return {'any_errors': True, 
            'message': f"number of assets {number_of_assets_str:s} isn\'t an integer"}


  # check the portfolio allocations
  for current_row in raw_portfolio_allocations:
    allocation_values: List = re.findall(r'\w+\.*\w*', current_row)

    for current_value in allocation_values:
      if not file_input_output.is_float(current_value):
        return {'any_errors': True, 
                'message': f"portfolio allocation {current_value:s} isn\'t a floating-point number"}


  # copy the portfolio allocations into a list of lists
  portfolio_allocations: List = [[] for x in range(len(raw_portfolio_allocations))]

  for current_item1, current_row in enumerate(raw_portfolio_allocations):
    allocation_values: List = re.findall(r'[-\+]*\w+\.*\w*', current_row)

    for current_value in allocation_values:
      portfolio_allocations[current_item1].append(float(current_value))


  # check that the allocations in each portfolio add up to 1.0
  for current_portfolio, current_allocations in enumerate(portfolio_allocations):
    total_allocations: float = sum(current_allocations)

    if abs(total_allocations - 1.0) > 0.001:
      return {'any_errors': True, 
              'message': f"portfolio {current_portfolio:d} allocations add up to {total_allocations:8.6f}"}


  return {'any_errors': False, 'message': '', 'allocations': portfolio_allocations}



def create_random_portfolios(optimal_fs: np.ndarray, long_only_portfolio: bool) -> List:
  """
  This function will create random portfolios based on the one defined
   in the 'optimal_fs' numpy array.  It will use different approaches to
   calculate the random portfolios depending on whether or not the
   ones in the 'optimal_fs' array are only long positions, as opposed to
   being a combination of long and short positions.

  It will return a list of numpy arrays, containing the randomly-generated
   portfolios.

  Created on July 18, 2022
  """

  number_of_assets: int = optimal_fs.shape[0]

  computer_portfolio_allocations: List = []

  number_of_portfolios: int = 11

  for current_portfolio in range(number_of_portfolios):
    computer_portfolio_allocations.append([])

  for current_asset, current_allocation in enumerate(optimal_fs):
    if current_asset < number_of_assets:
      for current_portfolio in computer_portfolio_allocations:
        current_portfolio.append(current_allocation)


  # create some random portfolio allocations around the one with the 
  #  optimal allocations
  for current_item in range(number_of_portfolios):
    assets_to_vary: List = random.sample([x for x in range(number_of_assets)], 2)
    variance_size: float = random.random()

    if long_only_portfolio:
      if computer_portfolio_allocations[current_item][assets_to_vary[1]] <= \
         computer_portfolio_allocations[current_item][assets_to_vary[0]]:
        if computer_portfolio_allocations[current_item][assets_to_vary[0]] - variance_size < 0.0:
          computer_portfolio_allocations[current_item][assets_to_vary[1]] = \
            computer_portfolio_allocations[current_item][assets_to_vary[1]] + \
            computer_portfolio_allocations[current_item][assets_to_vary[0]]
          computer_portfolio_allocations[current_item][assets_to_vary[0]] = 0.0
        else:
          computer_portfolio_allocations[current_item][assets_to_vary[0]] = \
            computer_portfolio_allocations[current_item][assets_to_vary[0]] - variance_size
          computer_portfolio_allocations[current_item][assets_to_vary[1]] = \
            computer_portfolio_allocations[current_item][assets_to_vary[1]] + variance_size
      else:
        if computer_portfolio_allocations[current_item][assets_to_vary[1]] - variance_size < 0.0:
          computer_portfolio_allocations[current_item][assets_to_vary[0]] = \
            computer_portfolio_allocations[current_item][assets_to_vary[0]] + \
            computer_portfolio_allocations[current_item][assets_to_vary[1]]
          computer_portfolio_allocations[current_item][assets_to_vary[1]] = 0.0
        else:
          computer_portfolio_allocations[current_item][assets_to_vary[1]] = \
            computer_portfolio_allocations[current_item][assets_to_vary[1]] - variance_size
          computer_portfolio_allocations[current_item][assets_to_vary[0]] = \
            computer_portfolio_allocations[current_item][assets_to_vary[0]] + variance_size
    else:
      computer_portfolio_allocations[current_item][assets_to_vary[1]] = \
        computer_portfolio_allocations[current_item][assets_to_vary[1]] - variance_size
      computer_portfolio_allocations[current_item][assets_to_vary[0]] = \
        computer_portfolio_allocations[current_item][assets_to_vary[0]] + variance_size


  return computer_portfolio_allocations



def calculate_optimal_fs(mean_returns: np.ndarray, 
                         covariance_matrix: np.ndarray, 
                         long_only_portfolio: bool) -> Dict:
  """
  This function will calculate the portfolio allocations needed to maximize
   the growth rate of the portfolio's value, under the assumptions that
   the assets' rates of growth are joint normally distributed and that
   the total of the allocations add up to 100%.

  Depending on the user's input, the portfolio will be constructed 
   assuming long and short positions can be held, or only long positions.
   
  It will return a dictionary with three keys.
  * 'any_errors', will be True if there are any problems and False if not.
  * 'message', will describe the problem, if there are any, or blank if
    there aren't any.
  * 'optimal_fs', will be blank if there are any problems or will be a 
    numpy array with the optimal fs if there aren't any problems.

  Created on June 20 and 22, July 3-4, and July 18, 2022
  """

  number_of_rows: int = covariance_matrix.shape[0]


  # calculate the optimal fs
  # if the user selects 'No' and if the matrix can be inverted, then you
  #  can just multiply some matrices.  otherwise, you need to try 
  #  quadratic programming.
  if not long_only_portfolio:
    # expand the arrays so they can be used to calculate the optimal fs if
    #  the user doesn't want a portfolio with only long positions.
    mean_returns_expanded: np.ndarray = np.vstack([mean_returns, [1]])

    covariance_matrix_addrow: np.ndarray = \
      np.vstack([covariance_matrix, np.ones(number_of_rows, dtype=np.float32)])
    covariance_matrix_expanded: np.ndarray = \
      np.hstack([covariance_matrix_addrow, np.ones((number_of_rows + 1, 1), dtype=np.float32)])
    covariance_matrix_expanded[number_of_rows, number_of_rows] = 0.0

#    print(mean_returns_expanded)
#    print(covariance_matrix_expanded)
#    time.sleep(6)

    if np.linalg.det(covariance_matrix_expanded) > 0:
      optimal_fs: np.ndarray = \
        np.matmul(np.linalg.inv(covariance_matrix_expanded), mean_returns_expanded)
      return {'any_errors': False, 'optimal_fs': optimal_fs[:number_of_rows].flatten()}

    constraint_A: np.ndarray = np.ones((2, number_of_rows))
    for current_column in range(number_of_rows):
      constraint_A[1, current_column] = -1.0

    constraint_b: np.ndarray = np.array([1.0, -1.0])

    try:
      results = quadprog.solve_qp(G=covariance_matrix, a=mean_returns.flatten(),
                                  C=constraint_A.T, b=constraint_b)

      return {'any_errors': False, 'optimal_fs': results[0]}
    except:
      return {'any_errors': True,
              'message': 'Quadratic programming function couldn\'t find answer.  Can\'t calculate portfolio allocations.'}
  else:
    constraint_A: np.ndarray = np.zeros((2 * number_of_rows + 1, number_of_rows))
    constraint_b: np.ndarray = np.zeros(2 * number_of_rows + 1)

    for current_column in range(number_of_rows):
      constraint_A[0, current_column] = 1.0

    constraint_b[0] = 1.0

    for current_row in range(1, number_of_rows + 1):
      constraint_A[current_row, current_row - 1] = -1.0
      constraint_b[current_row] = -1.0

    for current_row in range(number_of_rows + 1, 2 * number_of_rows + 1):
      constraint_A[current_row, current_row - number_of_rows - 1] = 1.0

    try:
      results = quadprog.solve_qp(G=covariance_matrix, a=mean_returns.flatten(),
                                  C=constraint_A.T, b=constraint_b, meq=1)

      return {'any_errors': False, 'optimal_fs': results[0]}
    except:
      return {'any_errors': True,
              'message': 'Quadratic programming function couldn\'t find answer.  Can\'t calculate portfolio allocations.'}



def get_type_portfolio_positions() -> str:
  """
  This function will ask the user if they want to build the optimal
   portfolio only using long positions in assets or using both short
   and long positions.

  The function will return a 'y' if the user wants the portfolio built
   only using long positions or 'n' if the user wants the portfolio to 
   be built with both long and short positions.

  Created on July 20, 2022
  """

  user_response: str = ''

  while not user_response:
    os.system('clear')

    print("The portfolio with the highest mean growth rate can be")
    print(" build using long and short stock/ETF positions, or it")
    print(" can be build only using long positions.")
    print("\nDo you want to build the portfolio only using long positions?")
    user_response = \
      input("\nEnter Yes or Y, No or N, or press Enter to return to the main menu: ")

    if not user_response:
      user_response = '-'
    elif user_response.lower() == 'yes' or user_response.lower() == 'y':
      user_response = 'y'
    elif user_response.lower() == 'no' or user_response.lower() == 'n':
      user_response = 'n'
    else:
      print("You must enter \'Yes\' or \'Y\' or \'No\' or \'N\' or press the Enter key")
      time.sleep(6)
      user_response = ''

  return user_response



def simulate_portfolio_values(portfolio_db: sqlite3.Connection):
  """
  This function will run a simulation.  It will create a set of portfolios,
   with allocations based on variations of the optimal portfolio (one of
   the portfolios will use the actual optimal allocations).  The function
   will then calculate the values of this set of portfolios over a number
   of trials.  The function will then print statistics on these simulations,
   by portfolio, to an output file.
   
  This simulation will, most of the time, show that the portfolio whose
   allocations are based on the optimal portfolio will have the highest
   growth rate.  The statistics will also show the downsides of building
   a portfolio with those allocations, such as high volatility and an
   increased chance of losing money in the short term.  This, again most
   of the time, will show why people with experience using the Kelly
   Criterion to allocate wealth to risky venture usually allocate some
   percent of the optimal f's to the risky assets.
  
  Created on June 6-13 and 20-23, 2022
  """

  os.system('clear')


  # simulation parameters and other information
  mean_returns: np.ndarray = database_input_output.get_mean_returns(portfolio_db)
  if mean_returns.shape[0] == 1:
    print("Need to import mean returns.")
    time.sleep(6)
    return

  mean_returns = mean_returns.flatten()

  covariance_matrix: np.ndarray = database_input_output.get_covariance_matrix(portfolio_db)
  if covariance_matrix.shape[0] == 1:
    print("Need to import covariance matrix.")
    time.sleep(6)
    return

  function_return: Dict = is_matrix_pos_semidef(covariance_matrix)
  if not function_return['pass_test']:
    print("The covariance matrix needs to be positive semi-definite to run the simulations.")
    print(f"{function_return['message']:s}")
    print("Can\'t run the simulation.")
    time.sleep(6)
    return

  number_of_assets: int = covariance_matrix.shape[0]

  test_portfolios: np.ndarray = database_input_output.get_portfolio_allocations(portfolio_db)
  if test_portfolios.shape[0] == 1:
    print("Need to calculate the portfolio allocations.")
    time.sleep(6)
    return

  number_of_portfolios: int = test_portfolios.shape[0]

  number_of_periods: int = 600
  number_of_sample_periods: int = 10
  length_of_sample_period: int = int(number_of_periods / number_of_sample_periods)
  number_of_runs: int = 10000
  starting_portfolio_value: float = 10000.0
# use to test the portfolio value calculation code
#  number_of_periods: int = 3
#  number_of_sample_periods: int = 3
#  length_of_sample_period: int = int(number_of_periods / number_of_sample_periods)
#  number_of_runs: int = 10


  # setup some of the arrays for the simulation
  value_assets: np.ndarray = np.zeros((number_of_portfolios, number_of_assets), dtype=np.float32)
  units_assets: np.ndarray = np.ones((number_of_portfolios, number_of_assets), dtype=np.float32)

  portfolio_values: np.ndarray = \
    np.zeros((number_of_portfolios, number_of_sample_periods, number_of_runs), dtype=np.float32)
  geometric_mean_returns: np.ndarray = \
    np.zeros((number_of_portfolios, number_of_runs), dtype=np.float32)

  portfolio_drawdown_factors: np.ndarray = np.array([0.5, 0.25, 0.10, 0.01])
  portfolio_drawdown_levels: np.ndarray = \
    np.ones((portfolio_drawdown_factors.shape[0]), dtype=np.float32)
  portfolio_drawdown_levels = np.multiply(portfolio_drawdown_factors, starting_portfolio_value)

  portfolio_drawdown_hits: np.ndarray = \
    np.zeros((number_of_portfolios, portfolio_drawdown_factors.shape[0], number_of_runs), dtype=np.int64)
  portfolio_drawdown_probabilities: np.ndarray = \
    np.zeros((number_of_portfolios, portfolio_drawdown_factors.shape[0]), dtype=np.float32)


  # the simulation
  progress_bar = tqdm.tqdm(total=number_of_runs)

  for current_run in range(number_of_runs):
    # set up the remaining arrays for the simulation
    price_assets: np.ndarray = np.ones(number_of_assets, dtype=np.float32)
    price_assets = price_assets * 100.0

    current_portfolio_value: np.ndarray = np.ones((number_of_portfolios, 1), dtype=np.float32)
    current_portfolio_value *= starting_portfolio_value

    # project the value of each portfolio over the time frame of the current run
    current_sample_period: int = 0
    for current_period in range(number_of_periods):

      # rebalance the portfolios
      units_assets = np.multiply(test_portfolios, current_portfolio_value)
      units_assets = np.divide(units_assets, price_assets)

      # calculate the new portfolio values
      return_assets: np.ndarray = np.random.multivariate_normal(mean_returns, covariance_matrix, 1)
      return_assets = np.add(return_assets, 1.0)
      price_assets = np.multiply(return_assets, price_assets)

      value_assets = np.multiply(units_assets, price_assets)

      current_portfolio_value[...,0] = np.sum(value_assets, axis=1)
      current_portfolio_value = \
        np.fmax(np.zeros((number_of_portfolios, 1)), current_portfolio_value)

      if current_period % length_of_sample_period == 0:
        portfolio_values[...,current_sample_period,current_run] = \
          np.sum(current_portfolio_value, axis=1)
        current_sample_period += 1

# use to test the portfolio value calculation code
#  and comment out the call to 'print_simulation_results'
#      if current_run == 0:
#        file_input_output.print_test_results(test_portfolios, units_assets,
#                                             price_assets, value_assets, 
#                                             current_portfolio_value, 
#                                             results_file)


    # check if the portfolio values hit the drawdown levels
    # is there a way to do this with numpy where functions instead of loop?
    for current_portfolio in range(number_of_portfolios):
      for current_index, current_level in enumerate(portfolio_drawdown_levels):
        if current_portfolio_value[current_portfolio, 0] <= current_level:
          portfolio_drawdown_hits[current_portfolio, current_index, current_run] = 1


    # record the geometric mean returns of the current run of the simulation
    geometric_mean_returns[...,current_run] = \
      np.sum(current_portfolio_value, axis=1) / starting_portfolio_value
    geometric_mean_returns[...,current_run] = \
      np.power(geometric_mean_returns[...,current_run], 1.0 / number_of_periods)
    geometric_mean_returns[...,current_run] = \
      np.subtract(geometric_mean_returns[...,current_run], np.ones(number_of_portfolios))

    progress_bar.update(1)


  progress_bar.close()


  portfolio_drawdown_probabilities = np.sum(portfolio_drawdown_hits, axis=2)
  portfolio_drawdown_probabilities = \
    np.divide(portfolio_drawdown_probabilities, float(number_of_runs))


  # calculate the statistics of the simulation and print them to the output file
  asset_returns_filepath: str = database_input_output.get_filepath('asset_returns', portfolio_db)
  user_portfolio_filepath: str = database_input_output.get_filepath('user_portfolios', portfolio_db)

  file_input_output.print_simulation_results(asset_returns_filepath, 
                                             user_portfolio_filepath,
                                             geometric_mean_returns, 
                                             portfolio_values, 
                                             {'number_of_runs': number_of_runs, 
                                              'number_of_periods': number_of_periods,
                                              'number_of_portfolios': number_of_portfolios,
                                              'length_of_sample_period': length_of_sample_period,
                                              'starting_portfolio_value': starting_portfolio_value},
                                             {'asset_mean_returns': mean_returns,
                                              'asset_covariance_matrix': covariance_matrix},
                                             portfolio_drawdown_levels, 
                                             portfolio_drawdown_probabilities,
                                             test_portfolios)

  return




if __name__ == "__main__":
  main()
