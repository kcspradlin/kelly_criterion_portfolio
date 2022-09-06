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
import sqlite3
#import time
import numpy as np



def get_asset_returns(portfolio_db: sqlite3.Connection) -> np.ndarray:
  """
  This function will query the 'asset_returns' table in the 
   'portfolio_db' database for its contents, and then put them into a
   numpy array, which will be returned to the calling function.

  Created on August 13, 2022
  """

  # first, get the number of assets and time periods in the 
  #  'asset_returns' table, in order to set up the numpy array
  db_cursor: sqlite3.Cursor = portfolio_db.cursor()

  count_query: str = 'select max(time_period), max(asset) from asset_returns;'

  db_cursor.execute(count_query)

  return_records = db_cursor.fetchone()

  if return_records[0] is not None and return_records[1] is not None:
    asset_returns: np.ndarray = np.zeros((return_records[0], return_records[1]), dtype=np.float32)
#    print(return_records[0])
#    print(return_records[1])
#    time.sleep(4)
  else:
    asset_returns: np.ndarray = np.zeros(1)
    return mean_returns


  # now, get the returns and then copy them into the numpy array
  select_query: str = 'select time_period, asset, return from asset_returns order by time_period, asset;'

  db_cursor.execute(select_query)

  return_records = db_cursor.fetchall()

  if return_records is not None:
    for current_record in return_records:
#      print(current_record[0])
#      print(current_record[1])
#      print(current_record[2])
#      time.sleep(2)
      asset_returns[current_record[0] - 1, current_record[1] - 1] = current_record[2]


  db_cursor.close()

  return asset_returns



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
    covar_matrix: np.ndarray = np.zeros(1)
    return covar_matrix


  # now, get the covariances and then copy them into the numpy array
  select_query: str = \
    'select asset1, asset2, var_covar from return_covariance_matrix order by asset1, asset2;'

  db_cursor.execute(select_query)

  return_records = db_cursor.fetchall()

  if return_records is not None:
    for current_record in return_records:
#      print(f"{current_record[0]:d}\t{current_record[1]:d}")
#      print(current_record[2])
      covar_matrix[current_record[0] - 1, current_record[1] - 1] = current_record[2]

  db_cursor.close()

  return covar_matrix



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
    mean_returns: np.ndarray = np.zeros(1)
    return mean_returns


  # now, get the returns and then copy them into the numpy array
  select_query: str = 'select asset, mean_return from mean_returns order by asset;'

  db_cursor.execute(select_query)

  return_records = db_cursor.fetchall()

  if return_records is not None:
    for current_record in return_records:
#      print(current_record[0])
#      print(current_record[1])
#      time.sleep(4)
      mean_returns[current_record[0] - 1, 0] = current_record[1]


  db_cursor.close()

  return mean_returns



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

    test_portfolios: np.ndarray = \
      np.zeros((return_records[0] + 1, return_records[1] + 1), dtype=np.float32)

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



def import_asset_returns(asset_return_data: np.ndarray, portfolio_db: sqlite3.Connection):
  """
  This function will take the data in the 'asset_return_data' numpy array and
  import each element into the 'asset_returns' table in the 'portfolio_db'
  database.

  Created on June 25-27, 2022
  """

  insert_query: str = 'insert into asset_returns(time_period, asset, return) values (?, ?, ?);'

  db_cursor: sqlite3.Cursor = portfolio_db.cursor()

  insert_records: List = []


  # put the data into insert_records list, then upload it to the 'asset_returns' table
  for current_period, current_returns in enumerate(asset_return_data):
    for current_asset, current_value in enumerate(current_returns):
      insert_records.append((current_period + 1, current_asset + 1, float(current_value), ))


  db_cursor.executemany(insert_query, insert_records)
  portfolio_db.commit()

  db_cursor.close()

  return



def import_covariance_matrix(covariance_matrix: np.ndarray, portfolio_db: sqlite3.Connection):
  """
  This function will take the data in the 'covariance_matrix' numpy array and
  import each element into the 'return_covariance_matrix' table in the 'portfolio_db' database.

  Created on June 19 and August 8, 2022
  """

  insert_query: str = 'insert into return_covariance_matrix(asset1, asset2, var_covar) values (?, ?, ?);'

  db_cursor: sqlite3.Cursor = portfolio_db.cursor()

  insert_records: List = []


  # put the data into insert_records list, then upload it to the 'return_covariance_matrix' table
  # note - for some reason, Python treats 'current_value' as a byte string.  need to run it through
  #        the float() function to get Python to treat it as a floating-point number.
  #        don't know why Python treats 'current_value' as a floating-point number in the
  #        'import_asset_returns' function.
  for current_asset1, current_row in enumerate(covariance_matrix):
    for current_asset2, current_value in enumerate(current_row):
      insert_records.append((current_asset1 + 1, current_asset2 + 1, float(current_value), ))


  db_cursor.executemany(insert_query, insert_records)
  portfolio_db.commit()

  db_cursor.close()

#  print(insert_records)

  return



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



def import_mean_covariance_matrices(asset_return_data: np.ndarray, 
                                    portfolio_db: sqlite3.Connection) -> Dict:
  """
  This function will calculate the means and covariances of the returns in the
   asset_return_data array.  It will then import them into the 'mean_returns' and  
   'return_covariance_matrix' tables in the database.

  It will return a dictionary with two keys:
  * 'any_errors', will be False if there are any problems or True if there are any
  * 'message', will be blank if there aren't any problems or will be a description
     of the problem if there is one

  Created on July 30-31, 2022
  """

  # first, calculate the mean returns and covariance matrix
  mean_returns: np.ndarray = np.mean(asset_return_data, axis=0)

  covariance_matrix: np.ndarray = np.cov(asset_return_data.T)

#  print(mean_returns)
#  print(mean_returns.shape)
#  print(covariance_matrix)
#  print(covariance_matrix.shape)
#  time.sleep(12)


  # now import the mean returns and covariance matrices into their tables
  #  in the database.
  insert_means_query: str = 'insert into mean_returns(asset, mean_return) values (?, ?);'
  insert_covariances_query: str = \
    'insert into return_covariance_matrix(asset1, asset2, var_covar) values (?, ?, ?);'

  db_cursor: sqlite3.Cursor = portfolio_db.cursor()


  # put the data into insert_records list and then upload it to the 'mean_returns' table
  insert_records: List = []

  for current_item, current_value in enumerate(mean_returns):
    insert_records.append((current_item + 1, float(current_value), ))


  db_cursor.executemany(insert_means_query, insert_records)
  portfolio_db.commit()
#  print(insert_records)


  # put the data into insert_records list and then upload it to the 'return_covariance_matrix' table
  insert_records = []

  for current_item1, current_row in enumerate(covariance_matrix):
    for current_item2, current_value in enumerate(current_row):
      insert_records.append((current_item1 + 1, current_item2 + 1, float(current_value), ))


  db_cursor.executemany(insert_covariances_query, insert_records)
  portfolio_db.commit()
#  print(insert_records)
#  time.sleep(12)


  db_cursor.close()

  return {'any_errors': False, 'message': ''}



def import_mean_returns(mean_returns: np.ndarray, portfolio_db: sqlite3.Connection):
  """
  This function will take the data in the 'mean_returns' numpy array and
  import each element into the 'mean_returns' table in the 'portfolio_db' database.

  Created on June 19 and August 8, 2022
  """

  insert_query: str = 'insert into mean_returns(asset, mean_return) values (?, ?);'

  db_cursor: sqlite3.Cursor = portfolio_db.cursor()

  insert_records: List = []


  # put the data into insert_records list, then upload it to the 'mean_returns' table
  for current_asset, current_value in enumerate(mean_returns):
    insert_records.append((current_asset + 1, float(current_value), ))


  db_cursor.executemany(insert_query, insert_records)
  portfolio_db.commit()

  db_cursor.close()

#  print(insert_records)

  return



def import_test_portfolios(portfolio_db: sqlite3.Connection, 
                           optimal_fs: np.ndarray, 
                           test_portfolio_allocations: List):
  """
  This function will the portfolios in the 'optimal_fs' array and the
   portfolios in the 'test_portfolio' list to the 'test_portfolios' table
   in the database.

  Created on July 18, 2022
  """

  # clear the current contents out of the 'test_portfolios' table
  delete_query_1: str = 'delete from test_portfolios;'
  delete_query_2: str = "delete from filepaths where description = 'user_portfolios';"

  db_cursor: sqlite3.Cursor = portfolio_db.cursor()

  db_cursor.execute(delete_query_1)
  db_cursor.execute(delete_query_2)
  portfolio_db.commit()


  # copy the new portfolios allocations to the 'test_portfolios' table.
  #  portfolio 0 will be the one with allocations that maximize the growth rate
  #  portfolios 1+ will either be the ones provided by the user or the ones
  #   generated by the computer.

  insert_query: str = 'insert into test_portfolios(portfolio, asset, allocation) values (?, ?, ?);'
  insert_records: List = []


  for current_item, current_value in enumerate(optimal_fs):
    insert_records.append((0, current_item, current_value, ))


  for current_portfolio, current_allocations in enumerate(test_portfolio_allocations):
    for current_asset, current_value in enumerate(current_allocations):
      insert_records.append((current_portfolio + 1, current_asset, current_value, ))


  db_cursor.executemany(insert_query, insert_records)
  portfolio_db.commit()

  db_cursor.close()

  return
