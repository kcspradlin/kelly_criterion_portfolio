### Readme
#### Last updated on August 13, 2022


##### Background

This project is focused on building a Python script that calculates portfolios 
consisting of one or more risky or risk-free assets, like stocks and ETFs.
The portfolios are constructed using the concept of the Kelly Criterion.

The Kelly Criterion comes out of a framework whose purpose is to find the
portion of someone's wealth that should be allocated to a repeated bet.
The goal in this framework is maximizing the growth rate of their wealth
over a period of time.  In a simple case, in which the payout of the bet
is determined by the toss of a coin, the formula for calculating the 
allocation to the bet is fairly simple.  A useful feature of the
framework is that it can be extended to a complicated case, such as having
the payouts come from returns on stocks, bonds, and other assets.  In
this complicated case, it's not as simple to find the portions of wealth
to allocate to the individual assets.

There are other approaches to determine how to allocate wealth over a set,
or portfolio, of assets.  One commonly-used approach uses the means,
variances, and correlations of the assets' returns to build a menu of 
possible portfolios from which an investor can choose.  The goal of this
approach is to find portfolios with the highest expected returns for a
specific amount of volatility in the portfolio's value (for more details,
read about Harry Markowitz's work in
[this press release](https://www.nobelprize.org/prizes/economic-sciences/1990/press-release/).

The Kelly Criterion approach uses the same asset return data and has
some similar assumptions, such as normally distributed asset returns.
However, it has a different goal: maximizing the expected growth rate of
the portfolio's value. 
<br>

##### Kelly Criterion Framework

To build the portfolio construction code for these scripts, I used the
framework described in Edward Thorp's "The Kelly Criterion in Blackjack
Sports Betting, and the Stock Market" paper in the book *The Kelly Capital
Growth Investment Criterion*, World Scientific Press, 2011.  I had to make
a change to the framework.  It wasn't set up to ensure that the allocations
to the assets in a portfolio (which are percentages of the portfolio's
total value) added up to 100%.  Also, I needed to change it to allow for
the possibility that the allocations for some assets could be negative.  I
eventually found a constrained optimization process that finds the desired
portfolio allocations.

##### Using the Script

Here are some instructions for using the 'kelly_criterion_portfolio.py' script.

First, you need to run the script from the command line.  The 
'database_input_output.py' and 'file_input_output.py' files need to be in
the same folder, since they have fucntions that are used by the 
'kelly_criterion_portfolio.py' script.

Second, I wrote it using Python 3.9.2, so I know that it works with that
version of Python.  There are some modules you'll need to install, and 
they're listed in the 'requirements.txt' file (you can install them using 
'python3 -m pip install -r requirements.txt from the command line).

Third, the script can read data from a file with the asset return statistics.
It has to have a specific format:

* the first line must have 'mean returns' on it
* the second line must have the mean excess returns of the assets, separated
  by spaces or tabs
* the fourth line must have 'covariance matrix' on it
* the fifth and later lines must have the covariance matrix.  one row from
  the matrix per line, with the variances and covariances separated by
  spaces or tabs.

The script can also read prices from a file and use that data to calculate
the mean returns and covariances of the returns.  This file has to have a
specific format:

* the prices in each period need to be on one row and separated by tabs
* the prices on one row are assumed to come from the period (day, week, or
  any other interval of time) immediately after the period from which the
  prices on the row above it in the file came.

When you run the script, you'll be shown a menu with five choices.  Enter
a number from 1 to 5 to select one of the choices, or just hit the Enter
key to exit.  Each choice takes you to a new screen, asks you for
information and/or shows you something, and then brings you back to this
main menu.

Choice **1** will ask you to enter the directory in which the file with
asset mean returns and a covariance matrix is located.  Next it asks you
for the name of the file.  If it can find the directory and file, the 
script will read the contents of the file into an internal database.

Choice **2** will ask you to enter the directory in which the file with
asset prices is located.  Next it asks you for the name of the file.  If
it can find the directory and file, then the script will read the contents
of the file, calculate period-over-period returns using the prices, then 
calculate means and covariances of the returns, and finally store those 
returns, means, and covariances into an internal database.

Choice **3** displays the mean returns and the covariance matrix.  This
gives you a way to validate the data that the script will use to calculate
the portfolio allocations and to run the portfolio value simulations.  If
you haven't yet run Choice **1** or **2**, it will prompt you to run one
of them.  After six seconds, you will be taken back to the main menu.

Choice **4** will do several things.

* First, it will ask you if you want to construct a set of portfolio
allocations using the Kelly Criterion that require all allocations to be
positive (aka - long-only portfolio), or that allow some allocations to
be positive and some to be negative (aka - long-short portfolio).  
Enter 'Yes' or 'Y' if you want all of the allocations to be positive, or
'No' or 'N' if you want to allow some of the allocations to be negative.

* Second, it will ask you if you want the computer to generate additional
portfolios to test in a simulation, or if you want to import your own
portfolios.
  * If you have the computer generate portfolios, it will create
them by making small random changes to two randomly-selected assets' 
allocations in the Kelly Criterion portfolio.

  * If you import your own portfolios, you will be asked to enter the
directory in which a file with portfolio allocations is located.  Next it
asks you for the name of the file.  If it can find the directory and the 
file, the script will read the contents of the file.  Regardless of how 
it gets the portfolios, the script will copy them and the Kelly 
Criterion-based portfolio into an internal database.

* Lastly, the script will display up to six of the portfolios the computer
generates or you provide, along with the Kelly Criterion-based one.  After
twelve seconds, you will be taken back to the main menu.

Note: the script expects the file with portfolio allocations to have a
specific format:

* the first line must have 'number of assets' on it
* the second line must have the number of assets
* the fourth line must have 'portfolio allocations' on it
* the fifth and later lines must have the portfolio allocations you want
  to test.  each row has one portfolio's asset allocations, as decimals
  (so, 0.50 means put 50% of the portfolio's value in that asset).  the
  assets' allocations are split up into columns by putting spaces between
  each number.

Choice **5** runs some simulations.  It uses the mean returns and
covariance matrix to generate random asset returns, using a multivariate
normal distribution.  It will use the returns to simulate values of the
portfolios from Choice **3** 600 periods into the future.  In each period, 
the returns of the assets will be simulated, the portfolio's new value 
will be calculated, and then the portfolio will be rebalanced between the 
different assets.  After 600 periods, the geometric mean growth rates of 
the portfolios will be recorded.  The simulations will be repeated for a 
total 10,000 times.  At the end, statistics on each portfolio used in 
these simulations will be printed to a file named 
'multi-asset simulation_statistics_v' followed by a number.  These 
statistics include:

* mean, standard deviation, skewness, and kurtosis of geometric mean returns
* median of portfolio values at select periods.
* lowest 1% of portfolio values at select periods (1% VaR).
* the average of the portfolio values that are equal to or less than the
  lowest 1% of portfolio values at select periods (1% Conditional 
  VaR/Expected Shortfall)
* The probabilities that the portfolio values will reach specific
  portions of the starting portfolio value (this one's inspired by 
  section 3.3 of Thorp's "The Kelly Criterion in Blackjack..." paper).

##### Hints and Other Information

* I provided an example file named 'asset_return_statistics.txt'.  It
contains means, variances, and covariances of the weekly total returns of
the SPY, GLD, and IEF ETFs.  As of June 2022, the statistics are based on
almost 18 years of data.

* I also provided an example file named 'asset_price_data.txt'.  It
contains almost years of weekly prices (adjusted for splits and 
reinvested dividends) of the SPY, GLD, and IEF ETFs.  If you import it, 
the script's calculated means, variances, and covariances will be pretty
close to the ones in the 'asset_return_statistics.txt' file.

* In order to derive the formula for calculating the optimal portfolio
allocations, I needed to make the assumption that the squares of the
mean returns are small enough that they can be ignored.  If you use
weekly or more frequently-measured returns, then satisfying this
assumption will be pretty easy.

* If you want one of the assets to be a risk-free asset, like 3-month
Treasury bills, then in the 'asset_return_statistics.txt' file:
  - use its mean return, just like every other asset, in the row of mean
  returns.
  - use the product of the mean risk-free return and another asset's mean
  return for the risk-free asset's covariance in that asset.
  - use the square of the mean risk-free return for the risk-free asset's
  variance.

* You can measure the returns on a total-return basis, price-return basis,
or an excess-return basis.  (Just to make sure it's stated somewhere) if
you use an excess-return basis, then you can't use a risk-free asset.  Its
excess returns would have zero covariance with any other asset's excess
returns and would have zero variance.  The resulting row and column of 
zeros in the covariance matrix would cause *problems* with the method used
to calculate the optimal portfolio allocations.
  - An example of using excess returns to find a portfolio using the Kelly
  Criterion framework can be found in [another paper written by Edward Thorp, along with 
Louis Rotando](http://www.edwardothorp.com/wp-content/uploads/2016/11/TheKellyCriterionAndTheStockMarket.pdf).  
  - Here's a link that explains why many researchers use excess returns 
(it's in the 'Mathematical convenience of excess returns' section of this link): 
[stackexchange link](https://quant.stackexchange.com/questions/28418/interpretation-of-excess-return)
<br>

