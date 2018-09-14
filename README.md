twitter_bots
===

This is a package for preprocessing Twitter data collections in order to perform bot detection on Twitter using the methodology described in:

*Stukal, Denis, Sergey Sanovich, Richard Bonneau, and Joshua A. Tucker. (2017). "Detecting Political Bots on Russian Twitter." Big Data 5(4): 310-324.*

It also creates static Twitter snapshots for reproducible Twitter account coding, along the lines out papers:

* Sanovich, Sergey, Denis Stukal, and Joshua A. Tucker. (2018). “Turning the Virtual Tables: Government Strategies for Addressing Online Opposition with an Application to Russia.” *Comparative Politics* 50(3): 435-482.

* Stukal, Denis, Sergey Sanovich, Richard Bonneau, and Joshua A. Tucker. (2017). "Detecting Political Bots on Russian Twitter." *Big Data* 5(4): 310-324.

Installation
---
1. Clone or download this repository

2. Use `pip install` to install `pysmap` and `numpy`

Making Static Twitter Snapshots
---

This package allows one to process Twitter data stored in JSON format. 

Suppose, you have Twitter data from April 1 to April 3, 2017 stored in two data files: /Users/mydata1.json and /Users/mydata2.json.

Suppose also that the code repository is stored as /Users/twitter_bots.

1. Import the module:
```
import codecs, re, os, datetime, time, math, sys
import numpy as np
from pysmap import SmappDataset
sys.path.insert(0, '/Users/twitter_bots')
from twitter_bots import Twitter_accounts
```

2. Use `SmappDataset` function in `pysmap` to set up your data for processing:
```
dataset0 = SmappDataset(['json', '/Users/mydata1.json'])
dataset1 = SmappDataset(['json', '/Users/mydata2.json'])
```

3. Instantiate an object of Twitter_accounts class:
```
mycol = Twitter_accounts(dates = [('2017-04-01', '2017-04-03')])
```
The `dates` argument is a list of tuples of length 2, where the first element of the tuple specifies the start date and the second element specifies the last date for tweets to be processed. All dates must be specified in the 'yyyy-mm-dd' format.

4. Loop over the dataset. Specify the dataset as a list. Specify `['html']` for the `functions` argument.
```
mycol.loop([dataset0, dataset1], functions = ['html'], max_tweets = 'all')
```

In the case you have only one dataset called `mydataset`, you would run:
```
mycol.loop([mydataset], functions = ['html'], max_tweets = 'all')
```

The `functions` argument specifies what type of processing you want to perform on your data. The only type that is relevant for creating static Twitter snapshots is 'html' that must be specified as a string inside a list. 

5. Write out HTML files to the desired directory:
```
mycol.make_html(path = '/Users/htmls_directory', min_num_tw = 10, max_num_tw = 100)
```



