#twitter_bots

This is a package for preprocessing Twitter data collections in order to perform bot detection on Twitter using the methodology described in:

*Stukal, Denis, Sergey Sanovich, Richard Bonneau, and Joshua A. Tucker. (2017). "Detecting Political Bots on Russian Twitter." Forthcoming in Big Data*

It also allows you to create static Twitter snapshots for reproducible Twitter account coding, along the lines out papers:
* Sanovich, Sergey, Denis Stukal, and Joshua A. Tucker. (2017). “Turning the Virtual Tables: Government Strategies for Addressing Online Opposition with an Application to Russia.” *Forthcoming in Comparative Politics.*
* Stukal, Denis, Sergey Sanovich, Richard Bonneau, and Joshua A. Tucker. (2017). "Detecting Political Bots on Russian Twitter." *Forthcoming in Big Data*

###Installation
1. Clone or download this repository

2. Use `pip install` to install `pysmap` and `numpy`

###Making Static Twitter Snapshots

This package allows one to process Twitter data stored in JSON format. Suppose, you have Twitter data from April 1 to April 3, 2017 stored in /Users/mydata.json, and the code repository is stored as /Users/twitter_bots.

1. Import the module:
```
import codecs, re, os, datetime, time, math, sys
import numpy as np
from pysmap import SmappDataset
import pickle
sys.path.insert(0, '/Users/twitter_bots')
from twitter_bots import Twitter_accounts
```

2. Use `pysmap` to set up your data for processing:
```
dataset = SmappDataset(['json', '/Users/mydata.json'])
```

3. Instantiate an object of Twitter_accounts class:
```
mycol = Twitter_accounts(dates = [('2017-04-01', '2017-04-03')])
```

4. Loop over the dataset. Specify the dataset as a list. Specify `['html']` for the `functions` argument.
```
mycol.loop([dataset], functions = ['html'], max_tweets = 'all')
```

5. Write out HTML files to the desired directory:
```
mycol.make_html(path = '/Users/htmls_directory', min_num_tw = 10, max_num_of_tweets = 100)
```



