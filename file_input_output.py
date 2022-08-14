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

from typing import Dict, IO, List
import os
import time
import re
import numpy as np
import scipy.stats as stats




def calculate_cvars(portfolio_values: np.ndarray,
                    portfolio_values_percentile: np.ndarray) -> np.ndarray:
  """
  This function will calculate the conditional VaRs, or expected shortfalls,
   or conditional tail expectations, of the values under a given 
   percentile.

  Created on August 7, 2022
  """

  portfolio_values_percentile_reshape: np.ndarray = \
    portfolio_values_percentile.reshape((portfolio_values_percentile.shape[0],
                                          portfolio_values_percentile.shape[1], 1))

  below_percentile_values: np.ndarray = \
    np.where(portfolio_values < portfolio_values_percentile_reshape, portfolio_values, 0.0)
  below_percentile_counts: np.ndarray = \
    np.where(portfolio_values < portfolio_values_percentile_reshape, 1.0, 0.0)

  below_percentile_totals_num: np.ndarray = np.sum(below_percentile_values, axis=2)
  below_percentile_totals_den: np.ndarray = np.sum(below_percentile_counts, axis=2)
  cvars: np.ndarray = np.divide(below_percentile_totals_num, below_percentile_totals_den)

  return cvars



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
  user_provided_dir: str = ''

  while not user_provided_dir:
    os.system('clear')

    print(message_to_user)

    print("\nPlease enter the location of the directory")
    user_provided_dir = input(" with the file or press Enter to quit: ")

    if not user_provided_dir:
      return {'any_errors': True, 'message': 'User quit function'}

    if not os.path.isdir(user_provided_dir):
      print("\nThat directory can\'t be found.\n Try again, or press Enter to quit.")
      user_provided_dir = ''
      time.sleep(6)
    else:
      break


  if user_provided_dir[:-1] != '/':
    user_provided_dir = user_provided_dir + '/'


  # next get the file's name, and check that it exists and can be opened
  user_provided_file: str = ''

  while not user_provided_file:
    os.system('clear')

    user_provided_file = input("Please enter the name of the file, or press Enter to quit: ")

    if not user_provided_file:
      return {'any_errors': True, 'message': 'User quit function'}

    if not os.path.exists(user_provided_dir + user_provided_file):
      print("\nThat file can\'t be found.\n Try again, or press Enter to quit.")
      user_provided_file = ''
      time.sleep(6)
    else:
      break


  return {'any_errors': False, 'message': '',
          'filepath': user_provided_dir + user_provided_file}



def is_float(test_input) -> bool:
  """
  This function will return True if 'test_input' can be converted to a floating-point
  number and False if not.

  Created on June 19, 2022
  """

  try:
    __ = float(test_input)
    return True

  except:
    return False



def is_int(test_input) -> bool:
  """
  This function will return True if 'test_input' can be converted to an integer
  and False if not.

  Created on June 22, 2022
  """

  try:
    __ = int(test_input)
    return True

  except:
    return False



def parse_asset_price_data(asset_price_filepath: str) -> Dict:
  """
  This function will open the file using the 'asset_price_filepath' parameter and
  parse the data in the file.  if it has the expected format and if the data passes
  some checks, then the function will calculate period-over-period returns and save
  those returns to the 'asset_returns' table in the 'portfolio_db' database.  It will
  also save the file and directory in the 'filepaths' table.

  The function will:
  * verify that the numbers in the file are floating-point numbers
  * will set a return to zero if the denominator is zero.
  
  It will return a dictionary with three keys:
  * 'any_errors', will be False if there are any problems or True if there are any
  * 'message', will be blank if there aren't any problems or will be a description
     of the problem if there is one
  * 'asset_return_data' will be a 2-dimensional numpy array.  the first dimension will
    be the time periods and the second dimension will be the asset identifiers.  the
    values in the array will be the period-over-period returns.

  Created on July 25-27, 2022
  """

  asset_price_file: IO = open(asset_price_filepath, 'r')


  # first check the contents of the file.
  prior_period_prices: List = []
  number_of_time_periods: int = 0

  for line_number, current_line in enumerate(asset_price_file):
    current_period_prices: List = re.findall(r'\w+\.*\w*', current_line)

    for current_value in current_period_prices:
      if not is_float(current_value):
        asset_price_file.close()
        return {'any_errors': True,
                'message': f"price {current_value:s} in period {line_number:d} isn\'t a floating-point number"}

    if not prior_period_prices:
      for current_value in current_period_prices:
        prior_period_prices.append(float(current_value))

    else:
      condition_1: bool = (len(prior_period_prices) != len(current_period_prices))
      condition_2: bool = (len(current_period_prices) > 0)
      if condition_1 and condition_2:
        asset_price_file.close()
        return {'any_errors': True,
                'message': f"period {line_number:d} has {len(current_period_prices):d} prices but period {line_number - 1:d} has {len(prior_period_prices):d} prices"}

    number_of_time_periods += 1


  # next, line by line, read in the prices.  after the first line, calculate
  #  the returns and store them in the asset_return_data dictionary
  asset_return_data: np.ndarray = \
    np.zeros((number_of_time_periods - 1, len(prior_period_prices)), dtype=np.float32)

  prior_period_prices: List = []

  asset_price_file.seek(0)
  for line_number, current_line in enumerate(asset_price_file):
    current_period_prices: List = re.findall(r'\w+\.*\w*', current_line)

    if not prior_period_prices:
      for current_value in current_period_prices:
        prior_period_prices.append(float(current_value))
#        print(f"{line_number:d}\t{float(current_value):8.6f}")

    else:
      for asset_id, current_value in enumerate(current_period_prices):
        if abs(prior_period_prices[asset_id]) > 0.01:
          asset_return_data[line_number - 1, asset_id] = \
            float(current_value) / prior_period_prices[asset_id] - 1.0
        else:
          asset_return_data[line_number - 1, asset_id] = 0.0

        prior_period_prices[asset_id] = float(current_value)


  asset_price_file.close()
#  print(asset_return_data.shape)
#  time.sleep(5)

  return {'any_errors': False, 'message': '', 'asset_return_data': asset_return_data}



def parse_asset_return_file(asset_return_filepath: str) -> Dict:
  """
  This function will open the file using the 'asset_return_filepath' parameter
   and parse the data in the file.  

  It will return a dictionary with four keys:
  * 'any_errors', will be False if there are any problems or True if there are any
  * 'message', will be blank if there aren't any problems or will be a description
     of the problem if there is one
  * 'mean_returns' will be 1-D numpy array with the mean returns from the file.
  * 'covariance_matrix' will be a 2-D numpy array with the covariance matrix from
    the file

  Created on July 18 and August 8, 2022
  """

  asset_data_file: IO = open(asset_return_filepath, 'r')


  # copy the mean returns from the file into a numpy array
  number_mean_returns: int = 0
  mean_returns: np.ndarray = np.zeros(1, dtype=np.float32)

  line_from_file: str = asset_data_file.readline()
  if line_from_file == "mean returns\n":
    mean_return_data: str = asset_data_file.readline()

    mean_values: List = re.findall(r'\w+\.*\w*', mean_return_data)
    for current_value in mean_values:
      if not is_float(current_value):
        asset_data_file.close()
        return {'any_errors': True, 
                'message': f"mean return value {current_value:s} isn\'t a floating-point number"}


    number_mean_returns = len(mean_values)

    mean_returns: np.ndarray = np.zeros((number_mean_returns), dtype=np.float32)
    for current_item, current_value in enumerate(mean_values):
      mean_returns[current_item] = float(current_value)
#      print(f"{mean_returns[current_item]:8.6f}")

  else:
    return {'any_errors': True,
            'message': "\'mean_returns\' not found on first line"}


  # copy the covariance matrix from the file
  for __ in range(2):
    line_from_file = asset_data_file.readline()


  number_rows_covar_matrix:int = 0
  number_columns_covar_matrix: int = 0
  covariance_matrix: np.ndarray = np.zeros((1, 1), dtype=np.float32)

  if line_from_file == "covariance matrix\n":
    covariance_data: List = []

    while line_from_file:
      line_from_file = asset_data_file.readline()
      if line_from_file:
        covariance_data_row: List = []

        covariance_values: List = re.findall(r'\w+\.*\w*', line_from_file)

        for current_value in covariance_values:
          if not is_float(current_value):
            asset_data_file.close()
            return {'any_errors': True, 
                    'message': f"covariance value {current_value:s} isn\'t a floating-point number"}
          else:
            covariance_data_row.append(float(current_value))


        covariance_data.append(covariance_data_row)
        number_rows_covar_matrix += 1
        
        if number_columns_covar_matrix == 0:
          number_columns_covar_matrix = len(covariance_data_row)

        elif number_columns_covar_matrix != len(covariance_data_row):
          asset_data_file.close()
          return {'any_errors': True, 
                  'message': f"covariance matrix has one row with {number_columns_covar_matrix:d} values and another with {len(covariance_data_row):d} values"}


    covariance_matrix: np.ndarray = \
      np.zeros((number_rows_covar_matrix, number_columns_covar_matrix), dtype=np.float32)

    for current_row_number, current_row in enumerate(covariance_data):
      for current_col_number, current_value in enumerate(current_row):
        covariance_matrix[current_row_number, current_col_number] = current_value
#        print(f"{covariance_matrix[current_row_number, current_col_number]:8.6f}")

  else:
    return {'any_errors': True,
            'message': "\'covariance matrix\' not found on fourth line"}


  asset_data_file.close()


  # verify that the number of mean returns matches the number of rows in
  #  the covariance matrix.  a later check will ensure that the covariance
  #  matrix is square.
  if number_mean_returns != number_rows_covar_matrix:
    return{'any_errors': True, 
           'message': f"number of mean returns = {number_mean_returns:d}, number of rows in covariance matrix = {number_rows_covar_matrix:d}"}

  if number_rows_covar_matrix != number_columns_covar_matrix:
    return{'any_errors': True, 
           'message': f"number of rows in covariance matrix = {number_rows_covar_matrix:d}, number of columns in covariance matrix = {number_columns_covar_matrix:d}"}

  return {'any_errors': False, 'message': '',
          'mean_returns': mean_returns, 'covariance_matrix': covariance_matrix}



def print_simulation_results(asset_returns_filepath: str,
                             user_portfolio_filepath: str,
                             geometric_mean_returns: np.ndarray,
                             portfolio_values: np.ndarray,
                             simulation_parameters: Dict,
                             asset_return_parameters: Dict,
                             portfolio_drawdown_levels: np.ndarray,
                             portfolio_drawdown_probabilities: np.ndarray,
                             test_portfolios: np.ndarray):
  """
  This function will print the statistics on the geometric mean returns and on
   the percentiles of portfolio values.

  Created on June 6 and 20, July 10-13, July 20, 2022
  """

  # open the file that will hold the statistics.
  results_filename: str = get_current_statistics_filename()
  results_file: IO = open(results_filename, 'w')


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

    for current_variance in current_variance_vector:
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

  measurement_periods: List = \
    [x for x in range(0, simulation_parameters['number_of_periods'] + 1, simulation_parameters['length_of_sample_period'])]

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

  measurement_periods: List = \
    [x for x in range(0, simulation_parameters['number_of_periods'] + 1, simulation_parameters['length_of_sample_period'])]

  for current_period in range(1, 11):
    results_file.write(f"\n{measurement_periods[current_period]:d}")
    for current_item in portfolio_values_1_percentiles[...,current_period - 1]:
      results_file.write(f"\t{current_item:,.0f}")


  # calculate and print the CVaRs for the 1st percentile
  cvars: np.ndarray = calculate_cvars(portfolio_values, portfolio_values_1_percentiles)


  results_file.write("\n\nCVaR/Expected Shortfall at Lowest 1% of Portfolio Values")
  results_file.write("\n-------------------------------------")

  results_file.write("\nPeriod")

  results_file.write("\n0")
  for current_item in test_portfolios:
    results_file.write(f"\t{simulation_parameters['starting_portfolio_value']:,.0f}")

  measurement_periods: List = \
    [x for x in range(0, simulation_parameters['number_of_periods'] + 1, simulation_parameters['length_of_sample_period'])]

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





  results_file.close()

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



def validate_asset_return_data(mean_return_data: str, covariance_data: List) -> Dict:
  """
  This function will check if the data in the 'mean_return_data' string
   and 'covariance_data' list of strings has the expected formats and 
   passes some checks.

  It will return a dictionary with two values:
  * 'any_errors', will be False if there are any problems or True if there are any
  * 'message', will be blank if there aren't any problems or will be a description
     of the problem if there is one

  Created on July 18, 2022
  """

  number_mean_returns: int = 0
  number_rows_covar_matrix: int = -1
  number_columns_covar_matrix: int = -2

  # check the mean return data for any problems
  mean_values: List = re.findall(r'\w+\.*\w*', mean_return_data)
  for current_value in mean_values:
    if not is_float(current_value):
      return {'any_errors': True, 
              'message': f"mean return value {current_value:s} isn\'t a floating-point number"}

  number_mean_returns = len(mean_values)


  # check the covariance matrix
  for current_row in covariance_data:
    covariance_values: List = re.findall(r'\w+\.*\w*', current_row)

    for current_value in covariance_values:
      if not is_float(current_value):
        return {'any_errors': True, 
                'message': f"covariance value {current_value:s} isn\'t a floating-point number"}

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


  return {'any_errors': False, 'message': ''}

