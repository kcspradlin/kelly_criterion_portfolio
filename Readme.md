### Readme
#### Last updated on July 4, 2022


##### Background

This project is based around a Python script that calculates portfolios 
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

##### Using the Excess Return Script

Here are some instructions for using the script.

First, you need to run the scripts from the command line.

Second, you need to use Python 3.x to run it (it wrote it using Python 3.9.2)
and you need to make sure that these modules are installed:

* numpy
* scipy
* tqdm
* quadprog.

The script uses other modules, but these come with a standard Python 3.x
installation.  I installed all of these using pip, so I know that method works.

Third, the scripts will look for the asset return statistics in a file
named 'asset_return_statistics.txt'.  It has to a have a specific format:

* the first line must have 'mean returns' on it
* the second line must have the mean excess returns of the assets, separated
  by spaces or tabs
* the fourth line must have 'covariance matrix' on it
* the fifth and later lines must have the covariance matrix.  one row from
  the matrix per line, with the variances and covariances separated by
  spaces or tabs.

When you run the script, you'll be shown a menu with four choices.  Enter
a number from 1 to 4 to select one of the choices, or just hit the Enter
key to exit.  Each choice takes you to a new screen, asks you for
information and/or shows you something, and then brings you back to this
main menu.

Choice **1** will ask you to enter the location of the directory in which 
the 'asset_return_statistics.txt' file is located.  If it can find the
directory and this file, then the script will read the contents of the file
into an internal database.

Choice **2** displays the mean returns and the covariance matrix.  This
gives you a way to validate the data that the script is using to calculate
the portfolio allocations and to run the portfolio value simulations.  If
you haven't yet run Choice 1, it will prompt you to run it.  After six
seconds, you will be taken back to the main menu.

Choice **3** will do several things.

* First, it will ask you if you want to construct a set of portfolio
allocations using the Kelly Criterion that require all allocations to be
positive (aka - long-only portfolio), or that allow some allocations to
be positive and some to be negative (aka - long-short portfolio, amongst
other terms).  Enter 'Yes' or 'Y' if you want all of the allocations to
be positive, or 'No' or 'N' if you want to allow some of the allocations 
to be negative.

* Second, it will ask you if you want the computer to generate additional
portfolios to test in a simulation, or if you want to import your own
portfolios.  If you have the computer generate portfolios, it will create
them by making small random changes to two randomly-selected assets' 
allocations in the Kelly Criterion portfolio.  If you import your own
portfolios, you will be asked to enter the location of the directory in
which the 'test_portfolios.txt' file is located.  If it can find the
directory and the file, the script will read the contents of the file.
Regardless of the how it gets the portfolios, the script will copy them
and the Kelly Criterion-based portfolio into an internal database.

* Lastly, the script will display up to six of the portfolios the computer
generates or you provide, along with the Kelly Criterion-based one.  After
twelve seconds, you will be taken back to the main menu.

Note: the script expects the 'test_portfolios.txt' file to have a specific
format:

* the first line must have 'number of assets' on it
* the second line must have the number of assets
* the fourth line must have 'portfolio allocations' on it
* the fifth and later lines must have the portfolio allocations you want
  to test.  each row has one portfolio's asset allocations, as decimals
  (so, 0.50 means put 50% of the portfolio's value in that asset).  the
  assets' allocations are split up into columns by putting spaces between
  each number.

Choice **4** runs some simulations.  It uses the mean returns and
covariance matrix to generate random asset returns.  It will use them to
simulate values of the portfolios from Choice 3 into the future.  These
simulations will go 600 periods into the future.  In each period, the 
returns of the assets will be simulated, the portfolio's new value will
be calculated, and then the portfolio will be rebalanced between the 
different assets.  After 600 periods, the geometric mean growth rates of
the portfolios will be recorded.  The simulations will be repeated for a
total 10,000 times.  At the end, statistics on these simulations will
be printed to a file named 'mulit-asset simulation_statistics'. 

##### Hints and Other Information

* I provided an example of the 'asset_return_statistics.txt' file.  It
contains means, variances, and covariances of the weekly total returns of
the SPY, GLD, and IEF ETFs.  As of June 2022, the statistics are based on
almost 18 years of data.

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
<br>

