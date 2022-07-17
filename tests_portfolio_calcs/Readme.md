### Readme
#### Last updated on July 6, 2022


I used the files in this directory to check that the Python script's
'calculate_portfolio_statistics' function was correctly calculating 
portfolio values.  I uncommented two sets of code in the function, which
only projected the portfolio values for a few periods and printed the 
portfolio values, portfolio allocations, asset prices, and units of
assets to the 'multi-asset simulation_statistics' file.

The four 'excess_return_statistics...' files have the means and
covariance matrices of four sets of assets that the Python script used
to build the portfolios it simulated.

In the 'Test Results - Three Asset Portfolio - Excess Returns.ods'
LibreOffice spreadsheet, I set up four tabs, one for each set of assets.

* In columns B through G, I used each set of assets' means and covariance
matrix of returns to calculate the portfolio that produces the highest
geometric mean growth rate.  I checked that the Python script was 
correctly calculating them in cells Q6:S6.

* Columns J and K copied the information from the 
'multi-asset simulation_statistics' file, which was the results of the
calculations done in the 'calculate_portfolio_statistics' function.

* In columns Q through W, I independently recreated the calculations done
in the 'calculate_portfolio_statistics' function.

* Columns Y and Z calculate the smallest and largest differences between
the results of the calculations from the Python script and the results
of the calculations done on the tab in the LibreOffice spreadsheet.

* Columns AB and AC have the smallest and largest of the differences
in columns Y and Z.

For each of the four sets of assets, the differences between Python
script's and the LibreOffice's calculations were small enough, after
accounting for rounding errors, that I was confident that the Python
script's 'calculate_portfolio_statistics' function was correctly
calculating portfolio values.
