# uaic-porfolio-tracker
A [Heroku](heroku.com) hosted backend and HTML frontend that shows a portfolio chart for UAIC.

If you're here, you're probably looking for instructions, so I've written out a few docs below.

## Installation
The backend is currently hosted on my personal Heroku account. You can do the same if you want, just clone this repo and deploy it to Heroku. All the Procfile and requirements.txt and everything is already sorted. Read the Heroku Flask getting started (all you need is to push it, no setup required)

Alternatively, if you have a better way of hosting it, all the logic is contained in the `/app` directory. There's a Flask application there, which imports the logic from the `chart_data_builder` file.

The front end code can be found either on the Squarespace website or in `docs/chart.html`. You can also see it in action [here](https://demar42.github.io/uaic-porfolio-tracker/chart.html).

## Making Changes
Most changes can be made to just the front-end
### Changing cash holdings
In the front end code, the variable `totalCash` counts the amount of cash on hand + any invested cash. In future, we probably should just turn this into a hardcoded cash value since there's no way I can be bothered coding dividends/brokerage/etc.

### Changing the holdings
The second variable in the front end code is an array of objects. Copy and paste them to show new holdings. Dates need to be `YYYY-MM-DD` and tickers need to be the Yahoo finance tickers. 

Selling can _possibly_ be shown by doing negative quantities, but I'm not sure how well that will work. 

## How does it work?
1. The frontend takes the holidngs data and POSTs it to the `/get-chart` API endpoint.
2. The endpoint fetches the data from Yahoo finance for all of the tickers, as well as a NZDAUD currency cross
3. It then re-indexes all the data on a new timeline that includes every day. This means if a stock has a few blank days, they get filled in (preventing zeros)
4. Finally, it calculates the value at each day with a for loop that considers when a stock was bought/sold

This is returned as JSON data for the frontend to display.

## Further Steps (for development)
* Currently it only handles NZX and ASX stocks, with a hardcoded conversion from AUD to NZD, based on the `.AX` suffix on the ticker
* No functionality to deal with selling
* Percentage returns are really simple and likely flawed
