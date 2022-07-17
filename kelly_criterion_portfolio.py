#!/usr/bin/python3
#
#  kelly_criterion_portfolio_excessreturns.py
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


from typing import Dict, List, IO
import sqlite3
import os
import time
import re
import numpy as np
import quadprog
import random
import scipy.stats as stats
import tqdm



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
  """
  # set up a internal database that holds user-provided and 
  #  calculated asset return and portfolio data
  portfolio_db: sqlite3.Connection = sqlite3.connect(":memory:")
  set_up_portfolio_db(portfolio_db)



  # clear screen then print console menu then wait for user input
  console_menu: Dict = set_up_console_menu()
  user_input: str = '-'

  while user_input != '':
    os.system('clear')
    
    print("This application will estimate a portfolio's asset")
    print(" allocations and return statistics, based on information")
    print(" provided by the user, in order to maximize the growth")
    print(" rate of the portfolio\'s value.\n")
    
    for item_number, item_command in console_menu.items():
      print(f"{item_number:s}: {item_command[0]:s}")
  
  
    user_input = input("\nSelect a command, or press Enter to exit: ")

    if user_input == '':
      print("\nBye\n")
      portfolio_db.close()

      return
    elif user_input not in console_menu:
      print("\nYou must select one of the commands or just press Enter")
      time.sleep(3)
    else:
      if console_menu[user_input][1] in globals():
        globals()[console_menu[user_input][1]](portfolio_db)
      else:
        print("\nThe function for that command hasn't yet been set up.")
        time.sleep(3)

  
  portfolio_db.close()
  
  return



def set_up_portfolio_db(portfolio_db: sqlite3.Connection):
  """
  This function will set up tables in the portfolio_db database to 
   hold means and covariances of the assets in the portfoliio and the
   optimal allocations of funds to the assets in the portfolio. 
  If they already exist, then they will first be deleted.

  Created on June 20-22 and July 10, 2022
  """

  db_cursor: sqlite3.Cursor = portfolio_db.cursor()

  check_query: str = \
    "select name from sqlite_master where type = 'table' and name = '{0:s}';"

  drop_query: str = "drop table {0:s};"

  create_queries: Dict = \
    {'mean_returns': "create table mean_returns(asset integer, mean_return real, primary key(asset));",
     'return_covariance_matrix': "create table return_covariance_matrix(asset1 integer, asset2 integer, var_covar real, primary key(asset1, asset2));",
     'filepaths': "create table filepaths(description text, filepath text, primary key(description));",
     'test_portfolios': "create table test_portfolios(portfolio integer, asset integer, allocation real, primary key(portfolio, asset));"}

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
  
  console_menu: Dict = {}
  console_menu['1'] = ('Import asset return data into internal db', 'import_return_data', )
  console_menu['2'] = ('Display imported asset return data', 'show_return_data', )
  console_menu['3'] = ('Calculate portfolio allocations', 'calculate_portfolio_allocations', )
  console_menu['4'] = ('Estimate portfolio statistics', 'simulate_portfolio_values', )

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
  function_results = get_filename('Looking for the file with asset returns and covariances')
  if function_results['any_errors']:
    print(function_results['message'])
    time.sleep(6)
    return


  asset_return_filepath: str = function_results['filepath']


  # clear out the 'returns' table in the database.
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

  asset_data_file: IO = open(asset_return_filepath, 'r')


  # copy the mean returns and covariance matrix from the file
  line_from_file: str = asset_data_file.readline()
  if line_from_file == "mean returns\n":
    mean_return_data: str = asset_data_file.readline()
  else:
    return {'any_errors': True, 'message': "\'mean_returns\' not found on first line"}

  
  for counter in range(2):
    line_from_file = asset_data_file.readline()

  if line_from_file == "covariance matrix\n":
    covariance_data: List = []

    while len(line_from_file) > 0:
      line_from_file = asset_data_file.readline()
      if len(line_from_file) > 0:
        covariance_data.append(line_from_file)

  else:
    return {'any_errors': True, 'message': "\'covariance matrix\' not found on fourth line"}


  number_mean_returns: int = 0
  number_rows_covar_matrix: int = -1
  number_columns_covar_matrix: int = -2

  # check the mean return data for any problems
  mean_values: List = re.findall(f'\w+\.*\w*', mean_return_data)
  for current_value in mean_values:
    if not is_float(current_value):
      return {'any_errors': True, 'message': f"mean return value {current_value:s} isn\'t a floating-point number"}

  number_mean_returns = len(mean_values)


  # check the covariance matrix
  for current_row in covariance_data:
    covariance_values: List = re.findall(f'\w+\.*\w*', current_row)    

    for current_value in covariance_values:
      if not is_float(current_value):
        return {'any_errors': True, 'message': f"covariance value {current_value:s} isn\'t a floating-point number"}

  number_rows_covar_matrix = len(covariance_data)
  number_columns_covar_matrix = len(covariance_values)
  

  # verify that the number of mean returns matches the number of rows in
  #  the covariance matrix.  a later check will ensure that the covariance
  #  matrix is square.
  if number_mean_returns != number_rows_covar_matrix:
    return{'any_errors': True, 
           'message': f"number of mean returns = {number_mean_returns:d}, number of rows in covariance matrix = {number_rows_covar_matrix:d}"}

  if number_rows_covar_matrix != number_columns_covar_matrix:
    return{'any_errors': True, 
           'message': f"number of rows in covariance matrix = {number_rows_covar_matrix:d}, number of columns in covariance matrix = {number_columns_covar_matrix:d}"}


  # since there aren't any problems with the mean returns and covariance
  #  matrix data, save them to the database.  also, need the covariance
  #  matrix to be in the database in order to put it into a numpy array
  #  and perform the next set of tests.
  import_mean_returns(mean_return_data, portfolio_db) 
  import_covariance_matrix(covariance_data, portfolio_db)
  import_filepath('asset_returns', asset_return_filepath, portfolio_db)


  # check the covariance matrix.  if it's invertible and positive semi-definite,
  #  then import it into the database.
  covariance_matrix: np.ndarray = get_covariance_matrix(portfolio_db)

  if np.linalg.det(covariance_matrix) == 0:
    print("The covariance matrix isn\'t invertible, so the portfolio allocations can\'t be calculated.")
    print("Try different asset(s) or making small changes to the matrix elements.")
    time.sleep(6)


  function_return: typing.Dict = is_matrix_pos_semidef(covariance_matrix)
  if not function_return['pass_test']:
    print("The covariance matrix needs to be positive semi-definite to run the simulations.")
    print(f"{function_return['message']:s}")
    print("Try different asset(s) or making small changes to the matrix elements.")
    time.sleep(6)
    

  asset_data_file.close()

  return {'any_errors': False, 'message': ''}



def import_mean_returns(mean_return_data: str, portfolio_db: sqlite3.Connection):
  """
  This function will take the data in the 'mean_return_data' string, parse it
  with some regex, and import each element into the 'mean_returns' table in
  the 'portfolio_db' database.  It will check each element to ensure that it's
  a floating-point number.
  
  Created on June 19, 2022
  """

  insert_query: str = 'insert into mean_returns(asset, mean_return) values (?, ?);'

  db_cursor: sqlite3.Cursor = portfolio_db.cursor()

  insert_records: List = []

  
  # put the data into insert_records list, then upload it to the 'mean_returns' table
  mean_values: List = re.findall(f'[-\+]*\w+\.*\w*', mean_return_data)
  for current_item, current_value in enumerate(mean_values):
    if is_float(current_value):
      insert_records.append((current_item + 1, float(current_value), ))  


  db_cursor.executemany(insert_query, insert_records)
  portfolio_db.commit()

  db_cursor.close()	


  return



def import_covariance_matrix(covariance_data: List, portfolio_db: sqlite3.Connection):
  """
  This function will take the data in the 'covariance_data' list of strings,
  parse it with some regex, and import each element into the 'return_covariance_matrix'
  table in the 'portfolio_db' database.  It will check each element to ensure that it's
  a floating-point number.
  
  Created on June 19, 2022
  """

  insert_query: str = 'insert into return_covariance_matrix(asset1, asset2, var_covar) values (?, ?, ?);'

  db_cursor: sqlite3.Cursor = portfolio_db.cursor()

  insert_records: List = []

  
  # put the data into insert_records list, then upload it to the 'return_covariance_matrix' table
  for current_item1, current_row in enumerate(covariance_data):
    covariance_values: List = re.findall(f'[-\+]*\w+\.*\w*', current_row)    

    for current_item2, current_value in enumerate(covariance_values):
      if is_float(current_value):
        insert_records.append((current_item1 + 1, current_item2 + 1, float(current_value), ))  


  db_cursor.executemany(insert_query, insert_records)
  portfolio_db.commit()

  db_cursor.close()	


  return



def is_float(test_input) -> bool:
  """
  This function will return True if 'test_input' can be converted to a floating-point
  number and False if not.
  
  Created on June 19, 2022  
  """
  
  try:
    test_number = float(test_input)
    return True	  
	  
  except:
    return False
  
  

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
  matrix_dimensions: typing.List = list(test_matrix.shape)
  
  if len(matrix_dimensions) != 2:
    message = 'Matrix needs to have 2 dimensions'
    return {'pass_test': pass_test, 'message': message} 
  
  elif matrix_dimensions[0] != matrix_dimensions[1]:
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
      
  
  if len(message) > 0:
    return {'pass_test': pass_test, 'message': message}


  return {'pass_test': True, 'message': message}



def show_return_data(portfolio_db: sqlite3.Connection):
  """
  This function will display the asset return means and covariance matrix 
   provided by the user.  It can be used to verify the data that's being used
   by the portfolio construction algorithm.

  Created on June 20, 2022 
  """

  os.system('clear')


  # put the mean return and covariance matrix data into numpy arrays
  mean_returns: np.ndarray = get_mean_returns(portfolio_db)

  covariance_matrix: np.ndarray = get_covariance_matrix(portfolio_db)

  
  print("Mean returns")
  print(mean_returns)
  
  print("\nCovariance matrix")
  print(covariance_matrix)


  time.sleep(6)
  

  return



def get_mean_returns(portfolio_db: sqlite3.Connection) -> np.ndarray:  
  """
  This function will query the 'mean_returns' table in the 'portfolio_db'
   database for its contents, and then put them into a numpy array, which
   will be returned to the calling function.
  
  Created on June 20, 2022
  Modified on July 3, 2022 - removed dtype from mean_returns declaration,
   to get quadprog.solve_qp function to work.
  """  

  # first, get the number of assets in the 'mean_returns' table, in order
  #  to set up the numpy array
  db_cursor: sqlite3.Cursor = portfolio_db.cursor()  

  count_query: str = 'select max(asset) from mean_returns;'

  db_cursor.execute(count_query)

  return_records = db_cursor.fetchone()

  if return_records[0] is not None:
    mean_returns: np.ndarray = np.zeros((return_records[0], 1))
  else:
    mean_returns: np.ndarray = np.zeros(1.0)
    return mean_returns


  # now, get the returns and then copy them into the numpy array
  select_query: str = 'select asset, mean_return from mean_returns order by asset;'

  db_cursor.execute(select_query)

  return_records = db_cursor.fetchall()

  if return_records is not None:
    for current_record in return_records:
      mean_returns[current_record[0] - 1, 0] = current_record[1] 
  
  
  db_cursor.close()

  return mean_returns



def get_covariance_matrix(portfolio_db: sqlite3.Connection) -> np.ndarray:  
  """
  This function will query the 'return_covariance_matrix' table in the 
   'portfolio_db' database for its contents, and then put them into a
   numpy array, which will be returned to the calling function.
  
  Created on June 20, 2022
  Modified on July 3, 2022 - removed dtype from mean_returns declaration,
   to get quadprog.solve_qp function to work.
  """  

  # first, get the number of assets in the 'return_covariance_matrix' table,
  #  in order to set up the numpy array
  db_cursor: sqlite3.Cursor = portfolio_db.cursor()  

  count_query: str = 'select max(asset1), max(asset2) from return_covariance_matrix;'

  db_cursor.execute(count_query)

  return_records = db_cursor.fetchone()

  if return_records[0] is not None:
    covar_matrix: np.ndarray = np.zeros((return_records[0], return_records[1]))
  else:
    covar_matrix: np.ndarray = np.zeros(1.0)
    return covar_matrix


  # now, get the covariances and then copy them into the numpy array
  select_query: str = 'select asset1, asset2, var_covar from return_covariance_matrix order by asset1, asset2;'

  db_cursor.execute(select_query)

  return_records = db_cursor.fetchall()

  if return_records is not None:
    for current_record in return_records:
      covar_matrix[current_record[0] - 1, current_record[1] - 1] = current_record[2] 
  
  
  db_cursor.close()

  return covar_matrix



def calculate_portfolio_allocations(portfolio_db: sqlite3.Connection):
  """
  This function will calculate the portfolio allocations needed to maximize
   the growth rate of the portfolio's value, under the assumptions that
   the assets' rates of growth are joint normally distributed and that
   the total of the allocations add up to 100%.
  Then, it will calculate 11 portfolios to test the growth rate of this
   portfolio.
  Next, it will ask the user if they want to use these portfolios in the
   simulation or if they want to import some portfolio (up to 11) from
   the 'test_portfolios.txt' file.
  Regardless of the choice taken, the function will save these portfolios'
   allocations to the 'test_portfolios' table in the database.
  
  Created on June 20-22, and July 4 and 10, 2022  
  """
    
  # first, calculate the portfolio allocations that maximize the growth rate
  function_results: Dict = calculate_optimal_fs(portfolio_db)
  if function_results['any_errors']:
    print(f"{function_results['message']:s}")
    time.sleep(6)
    return
  else:
    optimal_fs: np.ndarray = function_results['optimal_fs']    
    long_only_portfolio: bool = function_results['long_only']


  number_of_assets: int = optimal_fs.shape[0]

  user_portfolio_allocations: List = []
  computer_portfolio_allocations: List = []


  # ask the user if they want to use test portfolios provided by them of
  #  if they want the function to generate some random portfolios.
  os.system('clear')

  user_choice: str = '-'

  user_choice = input("Do you want to provide portfolio allocations to test?\n (Y for yes or N or Enter key for no) ")


  if user_choice.lower() == 'y':
    user_choice = 'y'


    # get the file path of the file with the asset return data
    function_results = get_filename('Looking for the file with test portfolio allocations')
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
    else:
      user_portfolio_allocations = import_results['allocations']    
      import_filepath('user_portfolios', portfolio_allocation_filepath, portfolio_db)
    
  elif user_choice.lower() == 'n' or len(user_choice) < 1:
    # create some random portfolio allocations around the one with the fastest growth rate
    number_of_portfolios: int = 11
    
    for current_portfolio in range(number_of_portfolios):
      computer_portfolio_allocations.append(list())

    for current_asset, current_allocation in enumerate(optimal_fs):
      if current_asset < number_of_assets:
        for current_portfolio in computer_portfolio_allocations:
          current_portfolio.append(current_allocation)


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


  os.system('clear')


  # clear the current contents out of the 'test_portfolios' table
  delete_query: str = 'delete from test_portfolios;'

  db_cursor: sqlite3.Cursor = portfolio_db.cursor()
  
  db_cursor.execute(delete_query)
  portfolio_db.commit()


  # copy the new portfolios allocations to the 'test_portfolios' table.
  #  portfolio 0 will be the one with allocations that maximize the growth rate
  #  portfolios 1+ will either be the ones provided by the user or the ones
  #   generated by the computer.

  insert_query: str = 'insert into test_portfolios(portfolio, asset, allocation) values (?, ?, ?);'
  insert_records: List = []


  for current_item, current_value in enumerate(optimal_fs):
    insert_records.append((0, current_item, current_value, ))  


  if len(user_portfolio_allocations) > 0:
    for current_portfolio, current_allocations in enumerate(user_portfolio_allocations):
      for current_asset, current_value in enumerate(current_allocations):
        insert_records.append((current_portfolio + 1, current_asset, current_value, ))
  
  else:
    for current_portfolio, current_allocations in enumerate(computer_portfolio_allocations):
      for current_asset, current_value in enumerate(current_allocations):
        insert_records.append((current_portfolio + 1, current_asset, current_value, ))


  db_cursor.executemany(insert_query, insert_records)
  portfolio_db.commit()

  db_cursor.close()	


  # print the portfolio allocations to the screen
  if len(user_portfolio_allocations) > 0:
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
           

  print("\nOptimal portfolio allocations, and some optimization results\n")
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
    while len(line_from_file) > 0:
      line_from_file = portfolio_allocation_file.readline()
      if len(line_from_file) > 0:
        raw_portfolio_allocations.append(line_from_file)

  else:
    return {'any_errors': True, 'message': "\'portfolio allocations\' not found on fourth line"}  


  portfolio_allocation_file.close()


  # convert the number of assets to an integer
  if not is_int(number_of_assets_str): 
    return {'any_errors': True, 'message': f"number of assets {number_of_assets_str:s} isn\'t an integer"}

  number_of_assets: int = int(number_of_assets_str)


  # check the portfolio allocations
  for current_row in raw_portfolio_allocations:
    allocation_values: List = re.findall(f'\w+\.*\w*', current_row)    

    for current_value in allocation_values:
      if not is_float(current_value):
        return {'any_errors': True, 'message': f"portfolio allocation {current_value:s} isn\'t a floating-point number"}


  # copy the portfolio allocations into a list of lists
  portfolio_allocations: List = [list() for x in range(len(raw_portfolio_allocations))]

  for current_item1, current_row in enumerate(raw_portfolio_allocations):
    allocation_values: List = re.findall(f'[-\+]*\w+\.*\w*', current_row) 

    for current_item2, current_value in enumerate(allocation_values):
      portfolio_allocations[current_item1].append(float(current_value))


  # check that the allocations in each portfolio add up to 1.0
  for current_portfolio, current_allocations in enumerate(portfolio_allocations):
    total_allocations: float = sum(current_allocations)
    
    if abs(total_allocations - 1.0) > 0.001:
      return {'any_errors': True, 'message': f"portfolio {current_portfolio:d} allocations add up to {total_allocations:8.6f}"}
  

  return {'any_errors': False, 'message': '', 'allocations': portfolio_allocations}



def is_int(test_input) -> bool:
  """
  This function will return True if 'test_input' can be converted to an integer
  and False if not.
  
  Created on June 22, 2022  
  """
  
  try:
    test_number = int(test_input)
    return True	  
	  
  except:
    return False



def calculate_optimal_fs(portfolio_db: sqlite3.Connection) -> Dict:
  """
  This function will calculate the portfolio allocations needed to maximize
   the growth rate of the portfolio's value, under the assumptions that
   the assets' rates of growth are joint normally distributed and that
   the total of the allocations add up to 100%.

  Depending on the user's input, the portfolio will be constructed 
   assuming long and short positions can be held, or only long positions.
   
  It will return a dictionary with four keys.  One 'any_errors', will be
   True if there are any problems and False if not.  The second key,
   'message', will describe the problem, if there are any, or blank if
   there aren't any.  The third key, 'optimal_fs', will be blank if there
   are any problems or will be a numpy array with the optimal fs if there
   aren't any problems.  The fourth key, 'long_only', will be True if the
   user selected to create a portfolio composed only of long positions, 
   or False if the user selected to create a portfolio of long and short
   positions.

  Created on June 20 and 22 and July 3-4, 2022 
  """
  
  # put the mean return and covariance matrix data into numpy arrays
  mean_returns: np.ndarray = get_mean_returns(portfolio_db)
  if mean_returns.shape[0] == 1:
   return {'any_errors': True, 'message': 'Need to import mean returns.'}

  covariance_matrix: np.ndarray = get_covariance_matrix(portfolio_db)
  if covariance_matrix.shape[0] == 1:
   return {'any_errors': True, 'message': 'Need to import covariance matrix.'}
  
  number_of_rows: int = covariance_matrix.shape[0]


  # expand the arrays so they can be used to calculate the optimal fs
  mean_returns_expanded: np.ndarray = np.vstack([mean_returns, [1]])

  covariance_matrix_addrow: np.ndarray = np.vstack([covariance_matrix, np.ones(number_of_rows, dtype=np.float32)])
  covariance_matrix_expanded: np.ndarray = np.hstack([covariance_matrix_addrow, np.ones((number_of_rows + 1, 1), dtype=np.float32)])
  covariance_matrix_expanded[number_of_rows, number_of_rows] = 0.0


  # determine if the user wants the portfolio to be build only with long
  #  positions, or if both long and short positions are OK
  user_response: str = ''

  while user_response == '':
    os.system('clear')
    
    print("The portfolio with the highest mean growth rate can be")
    print(" build using long and short stock/ETF positions, or it")
    print(" can be build only using long positions.")
    print("\nDo you want to build the portfolio only using long positions?")
    user_response = input("\nEnter Yes or Y, or No or N: ")

    if len(user_response) < 1:
      print("You must enter \'Yes\' or \'Y\' or \'No\' or \'N\'")
      time.sleep(6)
      user_response = ''
    elif user_response.lower() == 'yes' or user_response.lower() == 'y':
      user_response = 'y'
    elif user_response.lower() == 'no' or user_response.lower() == 'n':
      user_response = 'n'
    else:
      print("You must enter \'Yes\' or \'Y\' or \'No\' or \'N\'")
      time.sleep(6)
      user_response = ''


#  print(mean_returns_expanded)
#  print(covariance_matrix_expanded)
#  time.sleep(6)


  # calculate the optimal fs
  # if the user selects 'No' and if the matrix can be inverted, then you
  #  can just multiply some matrices.  otherwise, you need to try 
  #  quadratic programming.
  if user_response == 'n':
    if np.linalg.det(covariance_matrix_expanded) > 0:
      optimal_fs: np.ndarray = np.matmul(np.linalg.inv(covariance_matrix_expanded), mean_returns_expanded)
      return {'any_errors': False, 'optimal_fs': optimal_fs[:number_of_rows].flatten(), 'long_only': False}  
    else:
      constraint_A: np.ndarray = np.ones((2, number_of_rows))
      for current_column in range(number_of_rows):
        constraint_A[1, current_column] = -1.0


      constraint_b: np.ndarray = np.array([1.0, -1.0]) 


      try:
        results = quadprog.solve_qp(G=covariance_matrix, a=mean_returns.flatten(),
                                    C=constraint_A.T, b=constraint_b)


        return {'any_errors': False, 'optimal_fs': results[0], 'long_only': False} 
      except:
        return {'any_errors': True, 'message': 'Quadratic programming function couldn\'t find answer.  Can\'t calculate portfolio allocations.'}   
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

      return {'any_errors': False, 'optimal_fs': results[0], 'long_only': True} 
    except:
      return {'any_errors': True, 'message': 'Quadratic programming function couldn\'t find answer.  Can\'t calculate portfolio allocations.'}   



def get_portfolio_allocations(portfolio_db: sqlite3.Connection) -> np.ndarray:  
  """
  This function will query the 'test_portfolios' table in the 'portfolio_db'
   database for its contents and then put them into a numpy array, which will
   be returned to the calling function.
   
  The rows of the array will be portfolios and the columns will be the
   allocations to an asset.
  
  Created on June 20, 22-23, 2022
  """  

  # first, get the number of portfolios and assets in the 'test_portfolios'
  #  table, in order to set up the numpy array
  db_cursor: sqlite3.Cursor = portfolio_db.cursor()  

  count_query: str = 'select max(portfolio), max(asset) from test_portfolios;'

  db_cursor.execute(count_query)

  return_records = db_cursor.fetchone()

  number_of_assets: int = 0

  if return_records is not None:
    # portfolio 0 has the optimal allocations.
    number_of_assets = return_records[1]
    
    test_portfolios: np.ndarray = np.zeros((return_records[0] + 1, return_records[1] + 1), dtype=np.float32)

#    print(test_portfolios.shape)

  else:
    test_portfolios: np.ndarray = np.zeros(1, dtype=np.float32)
    return test_portfolios


  # now, get the optimal fs and then copy them into the numpy array
  select_query: str = 'select portfolio, asset, allocation from test_portfolios;'

  db_cursor.execute(select_query)

  return_records = db_cursor.fetchall()

  if return_records is not None:
    for current_record in return_records:
      if current_record[1] <= number_of_assets:
        test_portfolios[current_record[0], current_record[1]] = current_record[2] 
  
  
  db_cursor.close()

  return test_portfolios



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
  asset_returns_filepath: str = get_filepath('asset_returns', portfolio_db)
  user_portfolio_filepath: str = get_filepath('user_portfolios', portfolio_db)

  mean_returns: np.ndarray = get_mean_returns(portfolio_db)
  if mean_returns.shape[0] == 1:
    print("Need to import mean returns.")
    time.sleep(6)
    return
  else:
    mean_returns = mean_returns.flatten()
  
  covariance_matrix: np.ndarray = get_covariance_matrix(portfolio_db)
  if covariance_matrix.shape[0] == 1:
    print("Need to import covariance matrix.")
    time.sleep(6)
    return

  function_return: typing.Dict = is_matrix_pos_semidef(covariance_matrix)
  if not function_return['pass_test']:
    print("The covariance matrix needs to be positive semi-definite to run the simulations.")
    print(f"{function_return['message']:s}")
    print("Can\'t run the simulation.")
    time.sleep(6)
    return

  number_of_assets: int = covariance_matrix.shape[0]

  test_portfolios: np.ndarray = get_portfolio_allocations(portfolio_db)
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

  portfolio_values: np.ndarray = np.zeros((number_of_portfolios, number_of_sample_periods, number_of_runs), dtype=np.float32)
  geometric_mean_returns: np.ndarray = np.zeros((number_of_portfolios, number_of_runs), dtype=np.float32)

  portfolio_drawdown_factors: np.ndarray = np.array([0.5, 0.25, 0.10, 0.01])
  portfolio_drawdown_levels: np.ndarray = np.ones((portfolio_drawdown_factors.shape[0]), dtype=np.float32)
  portfolio_drawdown_levels = np.multiply(portfolio_drawdown_factors, starting_portfolio_value)

  portfolio_drawdown_hits: np.ndarray = np.zeros((number_of_portfolios, portfolio_drawdown_factors.shape[0], number_of_runs), dtype=np.int64)
  portfolio_drawdown_probabilities: np.ndarray = np.zeros((number_of_portfolios, portfolio_drawdown_factors.shape[0]), dtype=np.float32)


  # the simulation
  results_filename: str = get_current_statistics_filename()
  results_file: IO = open(results_filename, 'w')
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
      current_portfolio_value = np.fmax(np.zeros((number_of_portfolios, 1)), current_portfolio_value)

      if current_period % length_of_sample_period == 0:
        portfolio_values[...,current_sample_period,current_run] = np.sum(current_portfolio_value, axis=1)
        current_sample_period += 1

# use to test the portfolio value calculation code
#  and comment out the call to 'print_simulation_results'
#      if current_run == 0:
#        print_test_results(test_portfolios, units_assets,
#                           price_assets, value_assets, 
#                           current_portfolio_value, results_file)


    # check if the portfolio values hit the drawdown levels
    # is there a way to do this with numpy functions instead of loop?
    for current_portfolio in range(number_of_portfolios):
      for current_index, current_level in enumerate(portfolio_drawdown_levels):
        if current_portfolio_value[current_portfolio, 0] <= current_level:
          portfolio_drawdown_hits[current_portfolio, current_index, current_run] = 1
      

    # record the geometric mean returns of the current run of the simulation
    geometric_mean_returns[...,current_run] = np.sum(current_portfolio_value, axis=1) / starting_portfolio_value
    geometric_mean_returns[...,current_run] = np.power(geometric_mean_returns[...,current_run], 1.0 / number_of_periods)
    geometric_mean_returns[...,current_run] = np.subtract(geometric_mean_returns[...,current_run], np.ones(number_of_portfolios))

    progress_bar.update(1)


  progress_bar.close()


  portfolio_drawdown_probabilities = np.sum(portfolio_drawdown_hits, axis=2)
  portfolio_drawdown_probabilities = np.divide(portfolio_drawdown_probabilities, float(number_of_runs))


  # calculate the statistics of the simulation and print them to the output file
  print_simulation_results(asset_returns_filepath, user_portfolio_filepath,
                           geometric_mean_returns, portfolio_values, 
                           {'number_of_runs': number_of_runs, 'number_of_periods': number_of_periods,
                            'number_of_portfolios': number_of_portfolios,
                            'length_of_sample_period': length_of_sample_period,
                            'starting_portfolio_value': starting_portfolio_value},
                           {'asset_mean_returns': mean_returns,
                            'asset_covariance_matrix': covariance_matrix},
                           portfolio_drawdown_levels, portfolio_drawdown_probabilities,
                           test_portfolios, results_file)


  results_file.close()

  return



def print_simulation_results(asset_returns_filepath: str,
                             user_portfolio_filepath: str, 
                             geometric_mean_returns: np.ndarray, 
                             portfolio_values: np.ndarray, 
                             simulation_parameters: Dict,
                             asset_return_parameters: Dict,
                             portfolio_drawdown_levels: np.ndarray,
                             portfolio_drawdown_probabilities: np.ndarray,
                             test_portfolios: np.ndarray,
                             results_file: IO):
  """
  This function will print the statistics on the geometric mean returns and on
   the percentiles of portfolio values.

  Created on June 6 and 20, July 10-13, 2022
  """
  # calculate the statistics of the geometric mean returns and portfolio values
  returns_statistics: np.ndarray = stats.describe(geometric_mean_returns, axis=1)
  portfolio_values_1_percentiles: np.ndarray = np.percentile(portfolio_values, q=1.0, axis=2)
  portfolio_values_50_percentiles: np.ndarray = np.percentile(portfolio_values, q=50.0, axis=2)


  # print general information
  results_file.write(f"Path to file with asset return statistics: {asset_returns_filepath:s}\n")

  if user_portfolio_filepath != 'not found':
    results_file.write(f"Path to file with user-provided portfolio allocations: {user_portfolio_filepath:s}\n")

  
  # print information on the simulation parameters
  results_file.write(f"\nNumber of simulation runs: {simulation_parameters['number_of_runs']:d}\n")
  results_file.write(f"Number of periods per run: {simulation_parameters['number_of_periods']:d}\n")
  results_file.write(f"Number of portfolios: {simulation_parameters['number_of_portfolios']:d}\n")


  # print information on the assets
  results_file.write("\nAsset mean returns:")
  for current_asset, current_mean in enumerate(asset_return_parameters['asset_mean_returns']):
    results_file.write(f"\nAsset {current_asset:d}: {100.0 * current_mean:6.4f}%")

  results_file.write("\n\nAsset covariance matrix:\n")
  for asset_1, current_variance_vector in enumerate(asset_return_parameters['asset_covariance_matrix']):
    results_file.write(f"\t{asset_1:d}")

  for asset_1, current_variance_vector in enumerate(asset_return_parameters['asset_covariance_matrix']):
    results_file.write(f"\n{asset_1:d}")

    for asset_2, current_variance in enumerate(current_variance_vector):
      results_file.write(f"\t{current_variance:8.6f}")
      

  # print statistics on the geometric mean returns
  results_file.write("\n\nStatistics on Geometric Mean Growth Rates")
  results_file.write("\n-----------------------------------------")

  results_file.write("\n\nAsset Allocations")
  for asset_number, asset_allocations in enumerate(test_portfolios.transpose()):
    results_file.write(f"\n* {asset_number:d}")

    for current_allocation in asset_allocations:
      results_file.write(f"\t{100.0 * current_allocation:6.4f}%")


  results_file.write("\nNumber of Samples")
  for current_item in test_portfolios:
    results_file.write(f"\t{returns_statistics[0]:d}")
 
  results_file.write("\nSample Means")
  for current_item in returns_statistics[2]:
    results_file.write(f"\t{100.0 * current_item:6.4f}%")

  results_file.write("\nSample Standard Deviations")
  for current_item in np.power(returns_statistics[3], 0.5):
    results_file.write(f"\t{100.0 * current_item:6.4f}%")

  results_file.write("\nSample Skewnesses")
  for current_item in returns_statistics[4]:
    results_file.write(f"\t{100.0 * current_item:6.4f}%")

  results_file.write("\nSample Kurtoses")
  for current_item in returns_statistics[5]:
    results_file.write(f"\t{100.0 * current_item:6.4f}%")


  # print the two percentiles of the portfolio values over the simulation's time horizon
  results_file.write("\nAsset Allocations")
  for asset_number, asset_allocations in enumerate(test_portfolios.transpose()):
    results_file.write(f"\n* {asset_number:d}")

    for current_allocation in asset_allocations:
      results_file.write(f"\t{100.0 * current_allocation:6.4f}%")


  results_file.write("\n\nMedian of Portfolio Values")
  results_file.write("\n-------------------------------------")

  results_file.write("\nPeriod")

  results_file.write("\n0")
  for current_item in test_portfolios:
    results_file.write(f"\t{simulation_parameters['starting_portfolio_value']:,.0f}")

  measurement_periods: List = [x for x in range(0, simulation_parameters['number_of_periods'] + 1, simulation_parameters['length_of_sample_period'])]

  for current_period in range(1, 11):
    results_file.write(f"\n{measurement_periods[current_period]:d}")
    for current_item in portfolio_values_50_percentiles[...,current_period - 1]:
      results_file.write(f"\t{current_item:,.0f}")


  results_file.write("\n\nLowest 1% of Portfolio Values")
  results_file.write("\n-------------------------------------")

  results_file.write("\nPeriod")

  results_file.write("\n0")
  for current_item in test_portfolios:
    results_file.write(f"\t{simulation_parameters['starting_portfolio_value']:,.0f}")

  measurement_periods: List = [x for x in range(0, simulation_parameters['number_of_periods'] + 1, simulation_parameters['length_of_sample_period'])]

  for current_period in range(1, 11):
    results_file.write(f"\n{measurement_periods[current_period]:d}")
    for current_item in portfolio_values_1_percentiles[...,current_period - 1]:
      results_file.write(f"\t{current_item:,.0f}")


  # calculate and print the CVaRs for the 1st percentile
  portfolio_values_1_percentiles_reshape: np.ndarray = \
    portfolio_values_1_percentiles.reshape((portfolio_values_1_percentiles.shape[0],
                                            portfolio_values_1_percentiles.shape[1], 1))

  lower_percentile_values: np.ndarray = \
    np.where(portfolio_values < portfolio_values_1_percentiles_reshape, portfolio_values, 0.0)
  lower_percentile_counts: np.ndarray = \
    np.where(portfolio_values < portfolio_values_1_percentiles_reshape, 1.0, 0.0)

  lower_percentile_totals_num: np.ndarray = np.sum(lower_percentile_values, axis=2)
  lower_percentile_totals_den: np.ndarray = np.sum(lower_percentile_counts, axis=2)
  cvars: np.ndarray = np.divide(lower_percentile_totals_num, lower_percentile_totals_den)


  results_file.write("\n\nCVaR/Expected Shortfall at Lowest 1% of Portfolio Values")
  results_file.write("\n-------------------------------------")

  results_file.write("\nPeriod")

  results_file.write("\n0")
  for current_item in test_portfolios:
    results_file.write(f"\t{simulation_parameters['starting_portfolio_value']:,.0f}")

  measurement_periods: List = [x for x in range(0, simulation_parameters['number_of_periods'] + 1, simulation_parameters['length_of_sample_period'])]

  for current_period in range(1, 11):
    results_file.write(f"\n{measurement_periods[current_period]:d}")
    for current_item in cvars[...,current_period - 1]:
      results_file.write(f"\t{current_item:,.0f}")


  # print the portfolio drawdown probabilities
  results_file.write("\n\nProbabilities of Portfolio Values Reaching Specific Values")
  results_file.write("\n-------------------------------------")

  results_file.write("\nPortfolio Value")
  
  for current_index, current_level in enumerate(portfolio_drawdown_levels):
    results_file.write(f"\n{current_level:,.0f}")
    for current_item in portfolio_drawdown_probabilities[...,current_index]:
      results_file.write(f"\t{100.0 * current_item:4.2f}%")
    




  return



def print_test_results(test_portfolios: np.ndarray,
                       units_assets: np.ndarray,
                       price_assets: np.ndarray,
                       value_assets: np.ndarray,
                       current_portfolio_value: np.ndarray,
                       results_file: IO):
  """
  Created on June 12 and 20-21, 2022
  """

  np.set_printoptions(formatter={'float': '{:0.5f}'.format})

  results_file.write("Allocation factors\n")
  for portfolio, current_factors in enumerate(test_portfolios):
    results_file.write(f"{portfolio:d}:\t{str(current_factors):s}\n")


  results_file.write("Units of the assets\n")
  for portfolio, current_units in enumerate(units_assets):
    results_file.write(f"{portfolio:d}:\t{str(current_units):s}\n")


  results_file.write("Prices of the assets\n")
  for asset, current_price in enumerate(price_assets):
    results_file.write(f"{asset:d}:\t{str(current_price):s}\n")
  
  
  results_file.write("Values of the assets\n")
  for portfolio, current_values in enumerate(value_assets):
    results_file.write(f"{portfolio:d}:\t{str(current_values):s}\n")
  
  
  results_file.write("Current portfolio value\n")
  for portfolio, current_values in enumerate(current_portfolio_value):
    results_file.write(f"{portfolio:d}:\t{str(current_values):s}\n")

  return



def get_filename(message_to_user: str) -> Dict:
  """
  This function will prompt the user to first select a directory that
   contains a file and then to provide the name of a file.  The 
   function will check that the directory exists and that the file
   exists.

  The function will return a dictionary with three possible keys.
  * 'any_errors' will be True if there are any problems or False otherwise.
  * 'message' will contain a message describing any problems or will be
    blank if there aren't any problems.
  * 'filepath' will contain the concatenation of the directory and file
    name if there aren't any problems.

  Created on July 10, 2022
  """

  # first, get the directory in which the file can be found and check
  #  that it exists
  user_provided_dir: str = '-'

  while user_provided_dir != '':
    os.system('clear')

    print(message_to_user)
    
    print("\nPlease enter the location of the directory")
    user_provided_dir = input(" with the file or press Enter to quit: ")

    if len(user_provided_dir) < 1:
      return {'any_errors': True, 'message': 'User quit function'}
    elif not os.path.isdir(user_provided_dir):
      print("\nThat directory can\'t be found.\n Try again, or press Enter to quit.")
      time.sleep(6)
    else:
      break


  if user_provided_dir[:-1] != '/':
    user_provided_dir = user_provided_dir + '/'


  # next get the file's name, and check that it exists and can be opened
  user_provided_file: str = '-'

  while user_provided_file != '':
    os.system('clear')
    
    user_provided_file = input("Please enter the name of the file, or press Enter to quit: ")

    if len(user_provided_file) < 1:
      return {'any_errors': True, 'message': 'User quit function'}
    elif not os.path.exists(user_provided_dir + user_provided_file):
      print("\nThat file can\'t be found.\n Try again, or press Enter to quit.")
      time.sleep(6)
    else:
      break


  return {'any_errors': False, 'message': '', 
          'filepath': user_provided_dir + user_provided_file}



def import_filepath(table_key: str, table_value: str, portfolio_db: sqlite3.Connection):
  """
  This function will import the table key and value into a new record in the
  'filepaths' table in the 'portfolio_db' database.
  
  Created on July 10, 2022
  """

  insert_query: str = 'insert into filepaths(description, filepath) values (?, ?);'

  db_cursor: sqlite3.Cursor = portfolio_db.cursor()

  db_cursor.execute(insert_query, (table_key, table_value, ))

  portfolio_db.commit()

  db_cursor.close()	

  return



def get_filepath(table_key: str, portfolio_db: sqlite3.Connection) -> str:  
  """
  This function will query the 'filepaths' table in the 'portfolio_db'
   database for the file path matching the key 'table_key'.  It will
   return the file path if the key exists or 'not found' if is doesn't
   exist.
  
  Created on July 10, 2022
  """  

  return_value: str = ''

  db_cursor: sqlite3.Cursor = portfolio_db.cursor()  

  select_query: str = 'select filepath from filepaths where description = ?;'


  db_cursor.execute(select_query, (table_key, ))

  return_records = db_cursor.fetchone()

  if return_records is None:
    return_value = 'not found'
  else:
    return_value = return_records[0]

  
  db_cursor.close()

  return return_value



def get_current_statistics_filename() -> str:
  """
  This function will search in the current directory for any files whose
   names begin with 'multi-asset_simulation_statistics_v'.  It will then
   find the largest number after the '_v' in the name.  It will 
   increment the number by one and return a string, for the new
   statistics filename, that begins with 'multi-asset_simulation_statistics_v'
   and ends with the incremented number.

  If it can't find any files whose names begin with 
   'multi-asset_simulation_statistics_v', the function will just return
   'multi-asset_simulation_statistics_v1'.

  Created on July 16, 2022
  """
  
  highest_number: int = 0


  all_files: List = os.listdir('./')

  for current_file in all_files:
    if len(current_file) > 35:
      if current_file[:35] == 'multi-asset_simulation_statistics_v':
        current_number: int = 0

        try:
          current_number = int(current_file[35:])
        except:
          current_number = 0

        if current_number > highest_number:
          highest_number = current_number


  if highest_number > 0:
    return f"multi-asset_simulation_statistics_v{highest_number + 1:d}"
  else:
    return "multi-asset_simulation_statistics_v1"



if __name__ == "__main__":
  main()

