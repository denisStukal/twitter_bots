from pysmap import SmappDataset
import datetime, time, re, math, os, requests, pickle
import numpy as np

class Twitter_accounts():
    
    def __init__(self, dates, account_subset = None):
        '''
        Collections as a list of collections. Dates as yyyy-mm-dd strings
        '''
        # Time-related attributes
        valid_dates = []
        for j in range(len(dates)):
            valid_dates.append((datetime.date(int(dates[j][0][:4]), int(dates[j][0][5:7]), int(dates[j][0][8:])), datetime.date(int(dates[j][1][:4]), int(dates[j][1][5:7]), int(dates[j][1][8:]))))
        self.valid_dates = valid_dates
        # get first and last date
        start_date = self.valid_dates[0][0]
        end_date = self.valid_dates[0][1]
        for tup in self.valid_dates:
            for el in tup:
                if el < start_date:
                    start_date = el
                if el > end_date:
                    end_date = el
        self.start_year = time.strptime(str(start_date), "%Y-%m-%d")[0]
        self.start_month = time.strptime(str(start_date), "%Y-%m-%d")[1]
        self.end_year = time.strptime(str(end_date), "%Y-%m-%d")[0]
        self.end_month = time.strptime(str(end_date), "%Y-%m-%d")[1]
        # Reference to collections and subsets
        self.account_subset = account_subset
        # References to storing sets and dictionaries
        self.days = set()
        self.all_tweet_ids = set()
        self.all_relevant_tweet_ids = set()
        self.all_relevant_account_ids = set()
        self.all_subset_ids = set()
        self.all_subset_tweet_ids = set()
    
    
    def _enumerate_months_(self):
        '''
        Internal function: enumerates of months of available data. 
        Returns a tuple of min and max month numbers.
        '''
        year_dif = self.end_year - self.start_year
        max_month = year_dif*12 + self.end_month
        min_month = self.start_month
        return (min_month, max_month)
    
    
    def _initialize_storage_(self, functions = None):
        '''
        Internal function: creates storing dics for loop(). functions argument is passed to loop()
        '''
        if functions is not None:
            if 'all' in functions:
                self.tw_per_month_per_account = {}
                min_month, max_month = self._enumerate_months_()
                for month_num in range(min_month,max_month+1):
                    self.tw_per_month_per_account[month_num] = {}
                self.tw_per_account = {}
                self.tw_per_day = {}
                self.id_lang_dict = {}
                self.active_days_per_account = {}
                self.account_creation_date = {}
                self.min_max_tweets_per_account = {}
                self.min_max_tweets_per_account_per_month = {}
                self.feature_dict = {}
                self.user_for_entropy_time_sorted_dict = {}
                self.static = {}
            else:
                if 'screen_name' in functions:
                    self.screen_names = {}
                if 'tw' in functions:
                    self.tw_per_account = {}
                if 'tw_time' in functions:
                    self.tw_per_month_per_account = {}
                    min_month, max_month = self._enumerate_months_()
                    for month_num in range(min_month,max_month+1):
                        self.tw_per_month_per_account[month_num] = {}
                    self.tw_per_day = {}
                if 'lang' in functions:
                    self.id_lang_dict = {}
                if 'days_account' in functions:
                    self.active_days_per_account = {}
                if 'creation' in functions:
                    self.account_creation_date = {}
                if 'features' in functions:
                    self.tw_per_account = {}
                    self.min_max_tweets_per_account = {}
                    self.min_max_tweets_per_account_per_month = {}
                    self.feature_dict = {}
                    self.user_for_entropy_time_sorted_dict = {}
                if 'html' in functions:
                    self.static = {}
    
    
    def loop(self, collections, functions = None, max_tweets = 'all'):
        '''
        Main function. Iterates over tweet collections and stores information.
        Possible functions include: tw, lang, days_account, creation, features, html.
        Returns None.
        '''
        self._initialize_storage_(functions = functions)
        # Start looping
        i = 0
        col_num = 0
        for collection in collections:
            col_num += 1
            print('Collection:', col_num)
            for tw in collection:
                i += 1               
                if max_tweets != 'all':
                    if i > int(max_tweets):      
                        break            
                # Do everything only if tw wasn't processed yet
                if tw['id_str'] not in self.all_tweet_ids:
                    self.all_tweet_ids.add(tw['id_str'])
                    # Do everything only if tw in the time-range
                    if self.is_in_time_range(tw):
                        self.all_relevant_tweet_ids.add(tw['id_str'])
                        self.all_relevant_account_ids.add(tw['user']['id_str'])
                        # Check if user_id is in the subset of ids provided (if any)
                        if self.account_subset is None or tw['user']['id_str'] in self.account_subset:
                            self.all_subset_tweet_ids.add(tw['id_str'])
                            self.all_subset_ids.add(tw['user']['id_str'])
                            tw_date_stamp = self.get_tw_date_stamp(tw)
                            self.update_days(tw, tw_date_stamp)
                            if functions is not None:
                                if 'all' in functions:
                                    self.update_tw_per_account(tw)      # tw
                                    self.update_tw_per_month_per_account(tw) # tw_time
                                    self.update_tw_per_day(tw, tw_date_stamp)  # tw_time
                                    self.update_languages(tw)
                                    self.update_active_days(tw, tw_date_stamp)
                                    self.update_account_creation_date(tw)  # creation
                                    self.update_min_max_tweets_per_account(tw)  # features
                                    self.update_min_max_tweets_per_account_per_month(tw) # features
                                    self.update_primary_features_dict(tw, tw_date_stamp) # features 
                                    self.update_user_for_entropy_time_sorted_dict(tw) # features
                                else:
                                    if 'screen_name' in functions:
                                        #self.update_screen_names(tw)
                                        self.update_screen_names_w_date(tw)
                                    if 'tw' in functions:
                                        self.update_tw_per_account(tw) 
                                    if 'tw_time' in functions:
                                        self.update_tw_per_month_per_account(tw)
                                        self.update_tw_per_day(tw, tw_date_stamp)
                                    if 'lang' in functions:
                                        self.update_languages(tw)
                                    if 'days_account' in functions:
                                        self.update_active_days(tw, tw_date_stamp)
                                    if 'creation' in functions:
                                        self.update_account_creation_date(tw)
                                    if 'features' in functions:
                                        self.update_tw_per_account(tw) # tw/features
                                        self.update_min_max_tweets_per_account(tw)  # features
                                        self.update_primary_features_dict(tw, tw_date_stamp) # features 
                                        self.update_user_for_entropy_time_sorted_dict(tw) # features
                                    if 'html' in functions:
                                        self.update_static(tw)
        print('Looped over {0} tweets and {1} accounts in time range.\n {2} accounts and {3} tweets in the subset'.format(len(self.all_relevant_tweet_ids), len(self.all_relevant_account_ids), len(self.all_subset_ids), len(self.all_subset_tweet_ids)))
    
    
    def is_in_time_range(self, tw):
        '''
        Returns Boolean. True if a tweet creation date in the range of dates specified when instantiating a class object.
        '''
        tw_created_list = tw['created_at'].split(' ')
        time_obj = time.strptime('%s %s %s' % (tw_created_list[1], tw_created_list[2], tw_created_list[5]), "%b %d %Y")
        flag = False
        for tuple_num in range(len(self.valid_dates)):
            if datetime.date(time_obj[0], time_obj[1], time_obj[2]) >= self.valid_dates[tuple_num][0] and datetime.date(time_obj[0], time_obj[1], time_obj[2]) <= self.valid_dates[tuple_num][1]:
                flag  = True
        return flag
    
    
    def get_tw_date_stamp(self, tw):
        '''
        Returns a string with the date stamp for the current tweet in the form yyyy-mm-dd.
        '''
        tw_created_list = tw['created_at'].split(' ')
        time_obj = time.strptime('%s %s %s' % (tw_created_list[1], tw_created_list[2], tw_created_list[5]), "%b %d %Y")
        if time_obj[1] < 10:
            month = '0' + str(time_obj[1])
        else:
            month = str(time_obj[1])
        if time_obj[2] < 10:
            day = '0' + str(time_obj[2])
        else:
            day = str(time_obj[2])
        date_stamp = str(time_obj[0]) + '-' + month + '-' + day
        return date_stamp
    
    
    def get_acc_date_stamp(self, tw):
        '''
        Returns a string with the date stamp (yyyy-mm-dd) for the creation date of the userID who wrote the current tweet.
        '''
        tw_created_list = tw['user']['created_at'].split(' ')
        time_obj = time.strptime('%s %s %s' % (tw_created_list[1], tw_created_list[2], tw_created_list[5]), "%b %d %Y")
        if time_obj[1] < 10:
            month = '0' + str(time_obj[1])
        else:
            month = str(time_obj[1])
        if time_obj[2] < 10:
            day = '0' + str(time_obj[2])
        else:
            day = str(time_obj[2])
        date_stamp = str(time_obj[0]) + '-' + month + '-' + day
        return date_stamp
    
    
    def update_days(self, tw, date_stamp):
        '''
        Adds date stamp for a tweets to a set of all date stamps found.
        '''
        self.days.add(date_stamp)
    
    
    def update_tw_per_account(self, tw):
        '''
        Updates the count of tweets for the userID that produced the current tweet.
        Returns None. 
        '''
        if tw['user']['id_str'] not in self.tw_per_account:
            self.tw_per_account[tw['user']['id_str']] = 1
        else:
            self.tw_per_account[tw['user']['id_str']] += 1
    
    
    def update_tw_per_month_per_account(self, tw):
        '''
        Updates the monthly count of tweets for the userID that produced the current tweet.
        Returns None. 
        '''
        tw_created_list = tw['created_at'].split(' ')
        time_obj = time.strptime('%s %s %s' % (tw_created_list[1], tw_created_list[2], tw_created_list[5]), "%b %d %Y")
        year_dif = time_obj[0] - self.start_year
        current_month_num = year_dif*12 + time_obj[1]
        if tw['user']['id_str'] not in self.tw_per_month_per_account[current_month_num]:
            self.tw_per_month_per_account[current_month_num][tw['user']['id_str']] = 1
        else:
            self.tw_per_month_per_account[current_month_num][tw['user']['id_str']] += 1
    
    
    def update_languages(self, tw):
        '''
        Updates tweet and account language dictionaries, i.e. the counts of tweets written in specific language and with account interface in specific language.
        Returns None. 
        '''
        # Is userID in language dictionary?
        if tw['user']['id_str'] not in self.id_lang_dict:
            self.id_lang_dict[tw['user']['id_str']] = {}
            self.id_lang_dict[tw['user']['id_str']]['acc_lang'] = {}
            self.id_lang_dict[tw['user']['id_str']]['tw_lang'] = {}
        # Update the number of tweets written with the account having a specific interface language 
        if tw['user']['lang'] not in self.id_lang_dict[tw['user']['id_str']]['acc_lang']:
            self.id_lang_dict[tw['user']['id_str']]['acc_lang'][tw['user']['lang']] = 1
        else:
            self.id_lang_dict[tw['user']['id_str']]['acc_lang'][tw['user']['lang']] += 1
        # If tweet has detected language, update the number of tweets in a specific  language 
        if 'lang' in tw:
            if tw['lang'] not in self.id_lang_dict[tw['user']['id_str']]['tw_lang']:
                self.id_lang_dict[tw['user']['id_str']]['tw_lang'][tw['lang']] = 1
            else:
                self.id_lang_dict[tw['user']['id_str']]['tw_lang'][tw['lang']] += 1
    
    
    def update_active_days(self, tw, date_stamp):
        '''
        Update the set of day stamps for which the userID who wrote the current tweet has tweets in the collection.
        Returns None.
        '''
        if tw['user']['id_str'] not in self.active_days_per_account:
            self.active_days_per_account[tw['user']['id_str']] = set()
        self.active_days_per_account[tw['user']['id_str']].add(date_stamp)
    
    
    def update_screen_names(self, tw):
        '''
        Update set of screen_names associated with a given ID
        '''
        if tw['user']['id_str'] not in self.screen_names:
            self.screen_names[tw['user']['id_str']] = set()
        self.screen_names[tw['user']['id_str']].add(tw['user']['screen_name'])
    
    
    def update_screen_names_w_date(self, tw):
        '''
        Update set of screen_names associated with a given ID
        '''
        date_stamp = self.get_tw_date_stamp(tw)
        if tw['user']['id_str'] not in self.screen_names:
            self.screen_names[tw['user']['id_str']] = {date_stamp:tw['user']['screen_name']}
        else:
            if date_stamp not in self.screen_names[tw['user']['id_str']]:
                self.screen_names[tw['user']['id_str']][date_stamp] = tw['user']['screen_name']
    
    
    def update_account_creation_date(self, tw):
        '''
        Add account creation data for userID that was not found in the collection before. 
        Returns None.
        '''
        date_stamp = self.get_acc_date_stamp(tw)
        if tw['user']['id_str'] not in self.account_creation_date:
            self.account_creation_date[tw['user']['id_str']] = date_stamp
    
    
    def update_tw_per_day(self, tw, date_stamp):
        '''
        Updates tweet count per day.
        Returns None
        '''
        if date_stamp not in self.tw_per_day:
            self.tw_per_day[date_stamp] = 1
        else:
            self.tw_per_day[date_stamp] += 1
    
    
    def get_interface_language_percentages(self, language):
        '''
        Returns dictionary with percentages of tweets associated with different account interface languages.
        '''
        output = {}
        for account in self.id_lang_dict:
            if language in self.id_lang_dict[account]['acc_lang']:
                output[account] = self.id_lang_dict[account]['acc_lang'][language]/self.tw_per_account[account]*100
            else:
                output[account] = 0
        return output
    
    
    def get_tweet_language_percentages(self, language):
        '''
        Returns dictionary with percentages of tweets in different languages.
        '''
        output = {}
        for account in self.id_lang_dict:
            if language in self.id_lang_dict[account]['tw_lang']:
                output[account] = self.id_lang_dict[account]['tw_lang'][language]/self.tw_per_account[account]*100
            else:
                output[account] = 0
        return output
    
    
    def update_min_max_tweets_per_account(self, tw):
        '''
        For every account in the collection, computes the min and max number of tweets during data collection.
        Used to compute politicalness.
        Returns None.
        '''
        if tw['user']['id_str'] not in self.min_max_tweets_per_account:
            self.min_max_tweets_per_account[tw['user']['id_str']] = {}
            self.min_max_tweets_per_account[tw['user']['id_str']]['total_min'] = tw['user']['statuses_count']
            self.min_max_tweets_per_account[tw['user']['id_str']]['total_max'] = tw['user']['statuses_count']
        else:
            if tw['user']['statuses_count'] > self.min_max_tweets_per_account[tw['user']['id_str']]['total_max']:
                self.min_max_tweets_per_account[tw['user']['id_str']]['total_max'] = tw['user']['statuses_count']
            if tw['user']['statuses_count'] < self.min_max_tweets_per_account[tw['user']['id_str']]['total_min']:
                self.min_max_tweets_per_account[tw['user']['id_str']]['total_min'] = tw['user']['statuses_count']
    
    
    def make_politicalness(self):
        '''
        Produces politicalness dictionary. 
        Politicalness is defined as the numbrer of an accounts' tweets in the collection over the total number of tweets the account posted during data collection.
        The total number of accounts is approximated by subtracting the smallest total number of tweets from the largest total number of tweets from a given account's metadata. 
        Returns None.
        '''
        self.politicalness = {}
        # Get total number of tweets during data collection
        for el in self.min_max_tweets_per_account:
            if self.min_max_tweets_per_account[el]['total_max'] != self.min_max_tweets_per_account[el]['total_min']:
                self.min_max_tweets_per_account[el]['total_tw'] = self.min_max_tweets_per_account[el]['total_max'] - self.min_max_tweets_per_account[el]['total_min']
            else:
                self.min_max_tweets_per_account[el]['total_tw'] = 'NA'
        # Get politicalness
        for el in self.min_max_tweets_per_account:
            if self.min_max_tweets_per_account[el]['total_tw'] != 'NA':
                self.politicalness[el] = self.tw_per_account[el] / self.min_max_tweets_per_account[el]['total_tw']
            else:
                self.politicalness[el] = 'NA'
    
    
    def get_politicalness(self):
        '''
        Produces politicalness dictionary. 
        Politicalness is defined as the numbrer of an accounts' tweets in the collection over the total number of tweets the account posted during data collection.
        The total number of accounts is approximated by subtracting the smallest total number of tweets from the largest total number of tweets from a given account's metadata. 
        Returns dictionary.
        '''
        politicalness = {}
        # Get total number of tweets during data collection
        for el in self.min_max_tweets_per_account:
            if self.min_max_tweets_per_account[el]['total_max'] != self.min_max_tweets_per_account[el]['total_min']:
                self.min_max_tweets_per_account[el]['total_tw'] = self.min_max_tweets_per_account[el]['total_max'] - self.min_max_tweets_per_account[el]['total_min']
            else:
                self.min_max_tweets_per_account[el]['total_tw'] = 'NA'
        # Get politicalness
        for el in self.min_max_tweets_per_account:
            if self.min_max_tweets_per_account[el]['total_tw'] != 'NA':
                politicalness[el] = self.tw_per_account[el] / self.min_max_tweets_per_account[el]['total_tw']
            else:
                politicalness[el] = 'NA'
        return politicalness

    
    def update_min_max_tweets_per_account_per_month(self, tw):
        '''
        Updates the min and max number of tweets per month for a given account.
        Returns None.
        '''
        # set up storage for a new user_id
        if tw['user']['id'] not in  self.min_max_tweets_per_account_per_month:
            self.min_max_tweets_per_account_per_month[tw['user']['id']] = {}
            min_month, max_month = self._enumerate_months_()
            for month_num in range(min_month,max_month+1):
                self.min_max_tweets_per_account_per_month[tw['user']['id']][month_num] = {'time_1': 'NA', 'time_n': 'NA', 'time_1_numtw': 'NA', 'time_n_numtw': 'NA'}  
        # get current time stamp: time_obj[0] = year, time_obj[1] = month, time_obj[2] = day, time_obj[3] = hours, time_obj[4] = min, time_obj[5] = sec
        tw_created_list = tw['created_at'].split(' ')
        time_obj = time.strptime('%s %s %s %s' % (tw_created_list[1], tw_created_list[2], tw_created_list[5], tw_created_list[3]), "%b %d %Y %H:%M:%S")
        # get current month in the consecutive order of months under study
        year_dif = time_obj[0] - self.start_year
        current_month_num = year_dif*12 + time_obj[1]
        # if this month pops up for the 1st time
        if self.min_max_tweets_per_account_per_month[tw['user']['id']][current_month_num]['time_1'] == 'NA':
            self.min_max_tweets_per_account_per_month[tw['user']['id']][current_month_num]['time_1'] = time_obj
            self.min_max_tweets_per_account_per_month[tw['user']['id']][current_month_num]['time_n'] = time_obj
            self.min_max_tweets_per_account_per_month[tw['user']['id']][current_month_num]['time_1_numtw'] = tw['user']['statuses_count']
            self.min_max_tweets_per_account_per_month[tw['user']['id']][current_month_num]['time_n_numtw'] = tw['user']['statuses_count']
        else:
            # if current tw is an earlier one than time_1, update 'time_1' and 'time_1_numtw'
            if time_obj < self.min_max_tweets_per_account_per_month[tw['user']['id']][current_month_num]['time_1']:
                self.min_max_tweets_per_account_per_month[tw['user']['id']][current_month_num]['time_1'] = time_obj
                self.min_max_tweets_per_account_per_month[tw['user']['id']][current_month_num]['time_1_numtw'] = tw['user']['statuses_count']
            # if current tw is a later one than time_n, update 'time_n' and 'time_n_numtw'
            if time_obj > self.min_max_tweets_per_account_per_month[tw['user']['id']][current_month_num]['time_n']:
                self.min_max_tweets_per_account_per_month[tw['user']['id']][current_month_num]['time_n'] = time_obj
                self.min_max_tweets_per_account_per_month[tw['user']['id']][current_month_num]['time_n_numtw'] = tw['user']['statuses_count']
    
    
    def make_politicalness_per_account_per_month(self):
        '''
        Computes account's politicalness per month. 
        Returns None. 
        '''
        self.politicalness_per_account_per_month = {}
        # Get total number of tweets per month
        for acc in self.min_max_tweets_per_account_per_month:
            self.politicalness_per_account_per_month[acc] = {}
            for month in self.min_max_tweets_per_account_per_month[acc]:
                if self.min_max_tweets_per_account_per_month[acc][month]['time_n'] != 'NA':
                    self.min_max_tweets_per_account_per_month[acc][month]['total_tw'] = self.min_max_tweets_per_account_per_month[acc][month]['time_n_numtw'] - self.min_max_tweets_per_account_per_month[acc][month]['time_1_numtw']
                    self.min_max_tweets_per_account_per_month[acc][month]['num_days'] = self.min_max_tweets_per_account_per_month[acc][month]['time_n'][2] - self.min_max_tweets_per_account_per_month[acc][month]['time_1'][2]
                    if self.min_max_tweets_per_account_per_month[acc][month]['num_days'] > 15:
                        if self.min_max_tweets_per_account_per_month[acc][month]['total_tw'] != 0:
                            self.politicalness_per_account_per_month[acc][month] = self.tw_per_month_per_account[month][str(acc)] / self.min_max_tweets_per_account_per_month[acc][month]['total_tw']
                        else:
                            self.politicalness_per_account_per_month[acc][month] = 'NA'
                    else:
                        self.politicalness_per_account_per_month[acc][month] = 'UR'
                else:
                    self.politicalness_per_account_per_month[acc][month] = 'NA'
    
    
    def get_politicalness_per_account_per_month(self):
        '''
        Computes account's politicalness per month. 
        Returns dictionary. 
        '''
        politicalness_per_account_per_month = {}
        # Get total number of tweets per month
        for acc in self.min_max_tweets_per_account_per_month:
            politicalness_per_account_per_month[acc] = {}
            for month in self.min_max_tweets_per_account_per_month[acc]:
                if self.min_max_tweets_per_account_per_month[acc][month]['time_n'] != 'NA':
                    self.min_max_tweets_per_account_per_month[acc][month]['total_tw'] = self.min_max_tweets_per_account_per_month[acc][month]['time_n_numtw'] - self.min_max_tweets_per_account_per_month[acc][month]['time_1_numtw']
                    self.min_max_tweets_per_account_per_month[acc][month]['num_days'] = self.min_max_tweets_per_account_per_month[acc][month]['time_n'][2] - self.min_max_tweets_per_account_per_month[acc][month]['time_1'][2]
                    if self.min_max_tweets_per_account_per_month[acc][month]['num_days'] > 15:
                        if self.min_max_tweets_per_account_per_month[acc][month]['total_tw'] != 0:
                            politicalness_per_account_per_month[acc][month] = self.tw_per_month_per_account[month][str(acc)] / self.min_max_tweets_per_account_per_month[acc][month]['total_tw']
                        else:
                            politicalness_per_account_per_month[acc][month] = 'NA'
                    else:
                        politicalness_per_account_per_month[acc][month] = 'UR'
                else:
                    politicalness_per_account_per_month[acc][month] = 'NA'
        return politicalness_per_account_per_month
    
    
    def _is_retweet_(self, tweet):
        '''
        Takes a python-native tweet object (a dict). Returns True if a tweet is any kind of retweet.
        Returns Boolean.
        '''
        import re
        rt_manual_pattern = r"^RT @"
        rt_partial_pattern = r" RT @"
        if 'retweeted_status' in tweet:
            return True
        elif re.search(rt_manual_pattern, tweet['text']):
            return True
        elif re.search(rt_partial_pattern, tweet['text']):
            return True
        return False
    
    
    def _is_there_number_except_year_(self, screen_name): 
        '''
        Used in make_primary_features() to analyze user sceen_name. 
        Returns Boolean.
        '''
        if re.search(r'[0-9]+', screen_name):
            if not int(screen_name[re.search(r'[0-9]+', screen_name).start():re.search(r'[0-9]+', screen_name).end()]) >= 50 or not int(screen_name[re.search(r'[0-9]+', screen_name).start():re.search(r'[0-9]+', screen_name).end()]) <= 99:
                return True
        return False
    
    
    def _is_there_more_than_1_word_(self, name):
        '''
        Used in make_primary_features() to analyze user name. 
        Returns Boolean.
        '''
        if re.search(r' ', name):
            return True
        return False
    
    
    def update_primary_features_dict(self, tw, date_stamp):
        '''
        Stores data for Twitter static snapshots in dictionary feature_dict.
        Returns None. 
        '''
        # Function itself begins here:
        user_id = tw['user']['id_str']
        # created account
        datList = tw['user']['created_at'].split(' ')
        dat2 = '%s %s %s' % (datList[1], datList[2], datList[5])
        dt = datetime.datetime.strptime(dat2, '%b %d %Y')
        tw_dt = datetime.datetime.strptime(date_stamp, '%Y-%m-%d')
        # age at time of tweeting
        if dt != tw_dt:
            age = int(str(tw_dt-dt).split(' ')[0])
        else:
            age = 0
        if user_id not in self.feature_dict:  # 1 to the left
            self.feature_dict[user_id] = {}
            self.feature_dict[user_id]['date_first_tw_in_col'] = tw_dt
            self.feature_dict[user_id]['date_last_tw_in_col'] = tw_dt
            self.feature_dict[user_id]['age'] = age
            self.feature_dict[user_id]['total_tw_count'] = tw['user']['statuses_count']
            self.feature_dict[user_id]['count'] = 1
            self.feature_dict[user_id]['friends_count'] = []
            self.feature_dict[user_id]['friends_count'].append(tw['user']['friends_count'])
            self.feature_dict[user_id]['followers_count'] = []
            self.feature_dict[user_id]['followers_count'].append(tw['user']['followers_count'])
            self.feature_dict[user_id]['url_num'] = []
            self.feature_dict[user_id]['url_num'].append(len(tw['entities']['urls']))
            if len(tw['entities']['urls']) > 0:
                self.feature_dict[user_id]['num_tw_w_url'] = 1
            else:
                self.feature_dict[user_id]['num_tw_w_url'] = 0
            if self._is_retweet_(tw):
                self.feature_dict[user_id]['rt_num'] = 1
            else:
                self.feature_dict[user_id]['rt_num'] = 0
            if tw['user']['default_profile_image']:
                self.feature_dict[user_id]['default_profile_image'] = 1
            else:
                self.feature_dict[user_id]['default_profile_image'] = 0
            self.feature_dict[user_id]['default_profile_image_CHANGE'] = 0    
            if tw['user']['default_profile']:
                self.feature_dict[user_id]['default_theme_background_image'] = 1
            else:
                self.feature_dict[user_id]['default_theme_background_image'] = 0
            self.feature_dict[user_id]['default_theme_background_image_CHANGE'] = 0
            if not tw['user']['description']:
                self.feature_dict[user_id]['no_user_description'] = 1
                self.feature_dict[user_id]['user_description_length'] = 0
            else:
                self.feature_dict[user_id]['no_user_description'] = 0
                self.feature_dict[user_id]['user_description_length'] = len(tw['user']['description'])
            self.feature_dict[user_id]['user_description_CHANGE'] = 0
            self.feature_dict[user_id]['retweeted_accounts'] = set()
            if 'retweeted_status' in tw and not tw['retweeted_status'] is None:
                self.feature_dict[user_id]['retweeted_accounts'].add(tw['retweeted_status']['user']['id'])
            if self._is_there_number_except_year_(tw['user']['screen_name']):
                self.feature_dict[user_id]['digits_in_screen_name'] = 1    
            else:
                self.feature_dict[user_id]['digits_in_screen_name'] = 0
            if 'location' in tw['user'] and not tw['user']['location'] is None:
                if len(tw['user']['location']) > 0:
                    self.feature_dict[user_id]['location_specified'] = 1
            else:
                self.feature_dict[user_id]['location_specified'] = 0
            if self._is_there_more_than_1_word_(tw['user']['name']):
                self.feature_dict[user_id]['more_than_1_word_in_name'] = 1
            else: 
                self.feature_dict[user_id]['more_than_1_word_in_name'] = 0
            self.feature_dict[user_id]['favourites_count'] = []
            self.feature_dict[user_id]['favourites_count'].append(tw['user']['favourites_count'])
            self.feature_dict[user_id]['geo_enabled_CHANGE'] = 0
            if tw['user']['geo_enabled']:
                self.feature_dict[user_id]['geo_enabled'] = 1
            else:
                self.feature_dict[user_id]['geo_enabled'] = 0
            if re.search(r'#', tw['text']): 
                self.feature_dict[user_id]['tw_w_hash'] = 1
            else:
                self.feature_dict[user_id]['tw_w_hash'] = 0
            if re.search(r'@', tw['text']): 
                self.feature_dict[user_id]['tw_w_at'] = 1
            else:
                self.feature_dict[user_id]['tw_w_at'] = 0
            self.feature_dict[user_id]['num_hash'] = []
            self.feature_dict[user_id]['num_hash'].append(len(re.findall('#', tw['text'])))
            self.feature_dict[tw['user']['id_str']]['platform'] = {}
            self.feature_dict[tw['user']['id_str']]['platform'][tw['source']] = 1    
        else:
            self.feature_dict[user_id]['count'] += 1
            # take max of tweet counts for this user
            if tw['user']['statuses_count'] > self.feature_dict[user_id]['total_tw_count']:
                self.feature_dict[user_id]['total_tw_count'] = tw['user']['statuses_count']
            self.feature_dict[user_id]['friends_count'].append(tw['user']['friends_count'])
            self.feature_dict[user_id]['followers_count'].append(tw['user']['followers_count'])
            self.feature_dict[user_id]['url_num'].append(len(tw['entities']['urls']))
            if len(tw['entities']['urls']) > 0:
                self.feature_dict[user_id]['num_tw_w_url'] += 1
            if self._is_retweet_(tw):
                self.feature_dict[user_id]['rt_num'] += 1
            if tw['user']['default_profile_image'] and self.feature_dict[user_id]['default_profile_image'] == 0:
                self.feature_dict[user_id]['default_profile_image_CHANGE'] = 1
            if not tw['user']['default_profile_image'] and self.feature_dict[user_id]['default_profile_image'] == 1: 
                self.feature_dict[user_id]['default_profile_image_CHANGE'] = 1
            if tw['user']['default_profile'] and self.feature_dict[user_id]['default_theme_background_image'] == 0:
                self.feature_dict[user_id]['default_theme_background_image_CHANGE'] = 1
            if not tw['user']['default_profile'] and self.feature_dict[user_id]['default_theme_background_image'] == 1: 
                self.feature_dict[user_id]['default_theme_background_image_CHANGE'] = 1
            if not tw['user']['description'] and self.feature_dict[user_id]['no_user_description'] == 0:
                self.feature_dict[user_id]['user_description_CHANGE'] = 1
            if tw['user']['description'] and self.feature_dict[user_id]['no_user_description'] == 1:
                self.feature_dict[user_id]['user_description_CHANGE'] = 1
            if 'retweeted_status' in tw and not tw['retweeted_status'] is None:
                self.feature_dict[user_id]['retweeted_accounts'].add(tw['retweeted_status']['user']['id'])
            if self._is_there_number_except_year_(tw['user']['screen_name']):
                self.feature_dict[user_id]['digits_in_screen_name'] += 1    
            self.feature_dict[user_id]['favourites_count'].append(tw['user']['favourites_count'])
            if tw['user']['geo_enabled'] and self.feature_dict[user_id]['geo_enabled'] == 0:
                self.feature_dict[user_id]['geo_enabled_CHANGE'] = 1
            if re.search(r'#', tw['text']): 
                self.feature_dict[user_id]['tw_w_hash'] += 1
            if re.search(r'@', tw['text']): 
                self.feature_dict[user_id]['tw_w_at'] += 1
            self.feature_dict[user_id]['num_hash'].append(len(re.findall('#', tw['text'])))
            if tw['source'] in self.feature_dict[tw['user']['id_str']]['platform']:
                self.feature_dict[tw['user']['id_str']]['platform'][tw['source']] += 1
            else:
                self.feature_dict[tw['user']['id_str']]['platform'][tw['source']] = 1
    
    
    def update_user_for_entropy_time_sorted_dict(self, tw):
        '''
        Makes a list of all tweeting moments for each account. Used to compute entropy of inter-tweeting time intervals.
        Returns None.
        '''
        datList = tw['created_at'].split(' ')
        dat2 = '%s %s %s %s %s' % (datList[0], datList[1], datList[2], datList[3], datList[5])
        dt = datetime.datetime.strptime(dat2, '%a %b %d %H:%M:%S %Y')
        currentTime = time.mktime(dt.timetuple())
        if tw['user']['id_str'] in self.user_for_entropy_time_sorted_dict:
            self.user_for_entropy_time_sorted_dict[tw['user']['id_str']].append(currentTime)
        else:
            self.user_for_entropy_time_sorted_dict[tw['user']['id_str']] = [currentTime]
    
    
    def _make_probs_on_pauses_(self):
        '''
        Makes a dictionary with probs of pauses between consecutive tweets.
        Returns None.
        '''
        self.probs_on_pauses = {}
        for entry in self.user_for_entropy_time_sorted_dict:
                self.user_for_entropy_time_sorted_dict[entry].sort()
        usersPauses = {}
        for entry in self.user_for_entropy_time_sorted_dict:
            value = []
            for j in range(len(self.user_for_entropy_time_sorted_dict[entry])-1):
                value.append(self.user_for_entropy_time_sorted_dict[entry][j+1] - self.user_for_entropy_time_sorted_dict[entry][j])
            usersPauses[entry] = value
        # Fill in self.probs_on_pauses
        for entry in usersPauses:
            currentDic = {}
            # Take every int in the list of pauses
            for ob in usersPauses[entry]:
                if ob in currentDic:
                    currentDic[ob] += 1
                else:
                    currentDic[ob] = 1
            n = len(usersPauses[entry])
            value = []
            for key in currentDic:
                value.append(float(currentDic[key])/n)
            self.probs_on_pauses[entry] = value
    
    
    def make_entropy(self):
        '''
        1 argument - output from get_probs_on_pauses()
        Makes a dictionary with id_str as key and value = [entropy, number of DIFFERENT pauses ]
        Returns None
        '''
        self._make_probs_on_pauses_()
        self.entropy = {}
        for entry in self.probs_on_pauses:
            s = 0
            if len(self.probs_on_pauses[entry]) > 1:
                for num in self.probs_on_pauses[entry]:
                    s += num * math.log(num)
                    self.entropy[entry] = [-(float(s)/len(self.probs_on_pauses[entry])), len(self.probs_on_pauses[entry])]
            else:
                self.entropy[entry] = ['NA', 1]
    
    
    def get_final_feature_dict(self):
        '''
        Produces the final dictionary with data for bot detection. 
        Returns None. 
        '''
        self.final_feature_dict = {}
        if not hasattr(self, 'entropy'):
            self.make_entropy()
        if not hasattr(self, 'politicalness'):
            self.make_politicalness()
        for id in self.feature_dict:
            self.final_feature_dict[id] = {}
            self.final_feature_dict[id]['entropy'] = self.entropy[id][0]
            self.final_feature_dict[id]['total_tw_count'] = self.feature_dict[id]['total_tw_count']
            self.final_feature_dict[id]['count'] = self.feature_dict[id]['count']
            self.final_feature_dict[id]['tot_tw_over_count'] = self.final_feature_dict[id]['total_tw_count'] / self.final_feature_dict[id]['count']
            if self.feature_dict[id]['age'] == 0:
                self.final_feature_dict[id]['tot_tw_per_age'] = self.final_feature_dict[id]['total_tw_count']
            else:
                self.final_feature_dict[id]['tot_tw_per_age'] = self.final_feature_dict[id]['total_tw_count'] / self.feature_dict[id]['age']
            if self.politicalness[id] == 'NA':
                self.final_feature_dict[id]['politicalness'] = 0
            elif self.politicalness[id] >= 1:
                self.final_feature_dict[id]['politicalness'] = 1
            else: 
                self.final_feature_dict[id]['politicalness'] = self.politicalness[id]
            self.final_feature_dict[id]['url_prcnt'] = float(self.feature_dict[id]['num_tw_w_url']) / self.feature_dict[id]['count']
            self.final_feature_dict[id]['hash_prcnt'] = float(self.feature_dict[id]['tw_w_hash']) / self.feature_dict[id]['count']
            self.final_feature_dict[id]['at_prcnt'] = float(self.feature_dict[id]['tw_w_at']) / self.feature_dict[id]['count']
            self.final_feature_dict[id]['av_num_hash'] = np.mean(self.feature_dict[id]['num_hash'])
            self.final_feature_dict[id]['std_num_hash'] = np.std(self.feature_dict[id]['num_hash'])
            ratio_list = []
            for i in range(len(self.feature_dict[id]['followers_count'])):
                if self.feature_dict[id]['friends_count'][i] > 0:
                    ratio_list.append(float(self.feature_dict[id]['followers_count'][i]) / self.feature_dict[id]['friends_count'][i])
                #else:
                    #ratio_list.append('NA')
            if len(ratio_list) > 0:
                self.final_feature_dict[id]['av_ratio'] = np.mean(ratio_list)
                self.final_feature_dict[id]['no_friends'] = 0
            else:
                self.final_feature_dict[id]['av_ratio'] = 0
                self.final_feature_dict[id]['no_friends'] = 1
            self.final_feature_dict[id]['av_num_of_urls_per_tweet'] = np.mean(self.feature_dict[id]['url_num'])
            self.final_feature_dict[id]['std_num_of_urls_per_tweet'] = np.std(self.feature_dict[id]['url_num'])
            self.final_feature_dict[id]['max_num_of_urls_per_tweet'] = np.max(self.feature_dict[id]['url_num'])
            self.final_feature_dict[id]['default_profile_image'] = self.feature_dict[id]['default_profile_image']
            self.final_feature_dict[id]['default_profile_image_CHANGE'] = self.feature_dict[id]['default_profile_image_CHANGE']
            self.final_feature_dict[id]['default_theme_background_image'] = self.feature_dict[id]['default_theme_background_image']
            self.final_feature_dict[id]['default_theme_background_image_CHANGE'] = self.feature_dict[id]['default_theme_background_image_CHANGE']
            self.final_feature_dict[id]['no_user_description'] = self.feature_dict[id]['no_user_description']
            self.final_feature_dict[id]['user_description_length'] = self.feature_dict[id]['user_description_length']
            self.final_feature_dict[id]['user_description_CHANGE'] = self.feature_dict[id]['user_description_CHANGE']
            self.final_feature_dict[id]['rt_prcnt'] = float(self.feature_dict[id]['rt_num'])/self.feature_dict[id]['count']
            if int(self.feature_dict[id]['rt_num']) > 0:
                self.final_feature_dict[id]['accounts_retweeted_per_rt'] = float(len(self.feature_dict[id]['retweeted_accounts']))/self.feature_dict[id]['rt_num']
            else:
                self.final_feature_dict[id]['accounts_retweeted_per_rt'] = 0
            if self.feature_dict[id]['digits_in_screen_name'] > 0:
                self.final_feature_dict[id]['digits_in_screen_name'] = 1
            else:
                self.final_feature_dict[id]['digits_in_screen_name'] = 0
            if 'location_specified' in self.feature_dict[id]:
                self.final_feature_dict[id]['location_specified'] = self.feature_dict[id]['location_specified']
            else:
                self.final_feature_dict[id]['location_specified'] = 0
            self.final_feature_dict[id]['more_than_1_word_in_name'] = self.feature_dict[id]['more_than_1_word_in_name']
            if self.feature_dict[id]['total_tw_count'] > 0:
                self.final_feature_dict[id]['max_num_tweets_this_user_favored_over_total_tweets'] = np.max(self.feature_dict[id]['favourites_count']) / self.feature_dict[id]['total_tw_count']
            else:
                self.final_feature_dict[id]['max_num_tweets_this_user_favored_over_total_tweets'] = 0
            self.final_feature_dict[id]['geo_enabled_CHANGE'] = self.feature_dict[id]['geo_enabled_CHANGE'] 
            self.final_feature_dict[id]['geo_enabled'] = self.feature_dict[id]['geo_enabled'] 
            entropy = 0
            for source in self.feature_dict[id]['platform']:
                prct = float(self.feature_dict[id]['platform'][source])/self.feature_dict[id]['count']
                entropy += prct * np.log2(prct)
            self.final_feature_dict[id]['platform_entropy'] = - entropy
            # Specific platforms
            if '<a href="http://dlvr.it" rel="nofollow">dlvr.it</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['dlvr'] = float(self.feature_dict[id]['platform']['<a href="http://dlvr.it" rel="nofollow">dlvr.it</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['dlvr'] = 0
            if '<a href="http://ifttt.com" rel="nofollow">IFTTT</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['ifttt'] = float(self.feature_dict[id]['platform']['<a href="http://ifttt.com" rel="nofollow">IFTTT</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['ifttt'] = 0
            if '<a href="http://novosti.org" rel="nofollow">novosti_org</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['novosti'] = float(self.feature_dict[id]['platform']['<a href="http://novosti.org" rel="nofollow">novosti_org</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['novosti'] = 0
            if '<a href="http://twitter.com" rel="nofollow">Twitter Web Client</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['tw_web_client'] = float(self.feature_dict[id]['platform']['<a href="http://twitter.com" rel="nofollow">Twitter Web Client</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['tw_web_client'] = 0
            if '<a href="http://twitter.com/#!/download/ipad" rel="nofollow">Twitter for iPad</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['tw_ipad'] = float(self.feature_dict[id]['platform']['<a href="http://twitter.com/#!/download/ipad" rel="nofollow">Twitter for iPad</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['tw_ipad'] = 0
            if '<a href="http://twitter.com/download/android" rel="nofollow">Twitter for Android</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['tw_android'] = float(self.feature_dict[id]['platform']['<a href="http://twitter.com/download/android" rel="nofollow">Twitter for Android</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['tw_android'] = 0
            if '<a href="http://twitter.com/download/android" rel="nofollow">Twitter for  Android</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['tw_android2'] = float(self.feature_dict[id]['platform']['<a href="http://twitter.com/download/android" rel="nofollow">Twitter for  Android</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['tw_android2'] = 0
            if '<a href="http://twitter.com/download/iphone" rel="nofollow">Twitter for iPhone</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['tw_iphone'] = float(self.feature_dict[id]['platform']['<a href="http://twitter.com/download/iphone" rel="nofollow">Twitter for iPhone</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['tw_iphone'] = 0
            if '<a href="http://twitter.com/tweetbutton" rel="nofollow">Tweet Button</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['tw_button'] = float(self.feature_dict[id]['platform']['<a href="http://twitter.com/tweetbutton" rel="nofollow">Tweet Button</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['tw_button'] = 0
            if '<a href="http://twitterfeed.com" rel="nofollow">twitterfeed</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['twitterfeed'] = float(self.feature_dict[id]['platform']['<a href="http://twitterfeed.com" rel="nofollow">twitterfeed</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['twitterfeed'] = 0
            if '<a href="https://dev.twitter.com/docs/tfw" rel="nofollow">Twitter for Websites</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['tw_web'] = float(self.feature_dict[id]['platform']['<a href="https://dev.twitter.com/docs/tfw" rel="nofollow">Twitter for Websites</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['tw_web'] = 0
            if '<a href="https://mobile.twitter.com" rel="nofollow">Mobile Web (M2)</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['mobile_web_m2'] = float(self.feature_dict[id]['platform']['<a href="https://mobile.twitter.com" rel="nofollow">Mobile Web (M2)</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['mobile_web_m2'] = 0
            if '<a href="https://mobile.twitter.com" rel="nofollow">Mobile Web (M5)</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['mobile_web_m5'] = float(self.feature_dict[id]['platform']['<a href="https://mobile.twitter.com" rel="nofollow">Mobile Web (M5)</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['mobile_web_m5'] = 0
            if '<a href="https://twitter.com/download/android" rel="nofollow">Twitter for Android Tablets</a>' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['tw_android_tablets'] = float(self.feature_dict[id]['platform']['<a href="https://twitter.com/download/android" rel="nofollow">Twitter for Android Tablets</a>'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['tw_android_tablets'] = 0
            if 'web' in self.feature_dict[id]['platform']:
                self.final_feature_dict[id]['web'] = float(self.feature_dict[id]['platform']['web'])/self.final_feature_dict[id]['count']
            else: 
                self.final_feature_dict[id]['web'] = 0
    
    
    def get_subset(self, subset, selfdict):
        '''
        Returns a dict with accounts from selfdict that are also in subset.
        '''
        output = {}
        for acc in selfdict:
            if acc in subset:
                output[acc] = selfdict[acc]
        return output
    
    
    def update_static(self, tw):
        '''
        Uses current tweets to update information to be displayed in a Twitter static snapshot.
        Returns None. 
        '''
        user_id = tw['user']['id_str']
        text = re.sub(r'(\n)|(\r)', ' ', tw['text'])
        datList = tw['created_at'].split(' ')
        dat2 = '%s %s %s %s' % (datList[1], datList[2], datList[5], datList[3])
        dt = datetime.datetime.strptime(dat2, '%b %d %Y %H:%M:%S')
        date_time = str(dt)
        if user_id in self.static:
            self.static[user_id][date_time] = {}
            self.static[user_id][date_time]['text'] = text
            self.static[user_id][date_time]['name'] = tw['user']['name']
            self.static[user_id][date_time]['screen_name'] = tw['user']['screen_name']
            self.static[user_id][date_time]['tw_id'] = tw['id_str']
            self.static[user_id][date_time]['location'] = tw['user']['location']
            self.static[user_id][date_time]['profile_background_image_url'] = tw['user']['profile_background_image_url']
            self.static[user_id][date_time]['profile_image_url'] = tw['user']['profile_image_url']
            self.static[user_id][date_time]['default_profile'] = tw['user']['default_profile']
            self.static[user_id][date_time]['default_profile_image'] = tw['user']['default_profile_image']
            self.static[user_id][date_time]['statuses_count'] = tw['user']['statuses_count']
            self.static[user_id][date_time]['followers_count'] = tw['user']['followers_count']
            self.static[user_id][date_time]['friends_count'] = tw['user']['friends_count']
            creation_list = tw['user']['created_at'].split(' ')
            creation2 = '%s %s %s %s' % (creation_list[1], creation_list[2], creation_list[5], creation_list[3])
            creation_dt = datetime.datetime.strptime(creation2, '%b %d %Y %H:%M:%S')
            creation_date_time = str(creation_dt)
            self.static[user_id][date_time]['created_at'] = creation_date_time
            if tw['user']['description']:
                descr = re.sub(r'\n|\r|\t', ' ', tw['user']['description'])
                self.static[user_id][date_time]['description'] = descr
            else:
                self.static[user_id][date_time]['description'] = 'NA'
            if tw['user']['url']:
                self.static[user_id][date_time]['url'] = tw['user']['url']
            else:
                self.static[user_id][date_time]['url'] = 'NA'
            self.static[user_id][date_time]['favourites_count'] = tw['user']['favourites_count']
            self.static[user_id][date_time]['listed_count'] = tw['user']['listed_count']
        else:
            self.static[user_id] = {}
            self.static[user_id][date_time] = {}
            self.static[user_id][date_time]['text'] = text
            self.static[user_id][date_time]['name'] = tw['user']['name']
            self.static[user_id][date_time]['screen_name'] = tw['user']['screen_name']
            self.static[user_id][date_time]['tw_id'] = tw['id_str']
            self.static[user_id][date_time]['location'] = tw['user']['location']
            self.static[user_id][date_time]['profile_background_image_url'] = tw['user']['profile_background_image_url']
            self.static[user_id][date_time]['profile_image_url'] = tw['user']['profile_image_url']
            self.static[user_id][date_time]['default_profile'] = tw['user']['default_profile']
            self.static[user_id][date_time]['default_profile_image'] = tw['user']['default_profile_image']
            self.static[user_id][date_time]['statuses_count'] = tw['user']['statuses_count']
            self.static[user_id][date_time]['followers_count'] = tw['user']['followers_count']
            self.static[user_id][date_time]['friends_count'] = tw['user']['friends_count']
            creation_list = tw['user']['created_at'].split(' ')
            creation2 = '%s %s %s %s' % (creation_list[1], creation_list[2], creation_list[5], creation_list[3])
            creation_dt = datetime.datetime.strptime(creation2, '%b %d %Y %H:%M:%S')
            creation_date_time = str(creation_dt)
            self.static[user_id][date_time]['created_at'] = creation_date_time
            if tw['user']['description']:
                descr = re.sub(r'\n|\r|\t', ' ', tw['user']['description'])
                self.static[user_id][date_time]['description'] = descr
            else:
                self.static[user_id][date_time]['description'] = 'NA'
            if tw['user']['url']:
                self.static[user_id][date_time]['url'] = tw['user']['url']
            else:
                self.static[user_id][date_time]['url'] = 'NA'
            self.static[user_id][date_time]['favourites_count'] = tw['user']['favourites_count']
            self.static[user_id][date_time]['listed_count'] = tw['user']['listed_count']
    
    
    def make_html(self, path, min_num_tw, max_num_tw = 100):
        '''
        Produces HTML code for Twitter static snapshots. 
        Arguments: path - path to the folder where to write out HTML files;
            min_num_tw - how many tweets an account should have in the collection for the snapshot to be produced;
            max_num_tw - the largest number of tweets to reproduce in an account's snapshot.
        '''
        # check if path ends with a slash
        if path[len(path)-1] != '/':
            path = path + '/'
        # store latest available url etc for each id
        dic = {}
        for id in self.static:
            if len(self.static[id]) >= min_num_tw:
                dic[id] = {}
                for date_time in self.static[id]:
                    day = date_time.split()[0]
                    if day not in dic[id]:
                        dic[id][day] = {}
                    time = date_time.split()[1]
                    dic[id][day][time] = {}
                    dic[id][day][time]['tweet'] = self.static[id][date_time]['text']
                    dic[id][day][time]['name'] = self.static[id][date_time]['name']
                    dic[id][day][time]['screen_name'] = self.static[id][date_time]['screen_name']
                    dic[id][day][time]['tweet_id'] = self.static[id][date_time]['tw_id']
                    dic[id][day][time]['full_time'] = date_time
                    dic[id][day][time]['location'] = self.static[id][date_time]['location']
                    dic[id][day][time]['profile_background_image_url'] = self.static[id][date_time]['profile_background_image_url']
                    dic[id][day][time]['profile_image_url'] = self.static[id][date_time]['profile_image_url']
                    dic[id][day][time]['statuses_count'] = self.static[id][date_time]['statuses_count']
                    dic[id][day][time]['followers_count'] = self.static[id][date_time]['followers_count']
                    dic[id][day][time]['friends_count'] = self.static[id][date_time]['friends_count']
                    dic[id][day][time]['created_at'] = self.static[id][date_time]['created_at']
                    dic[id][day][time]['description'] = self.static[id][date_time]['description']
                    dic[id][day][time]['url'] = self.static[id][date_time]['url']
                    dic[id][day][time]['favourites_count'] = self.static[id][date_time]['favourites_count']
                    dic[id][day][time]['listed_count'] = self.static[id][date_time]['listed_count']
        # start writing out htmls
        for id in dic:
            profile_background_image_url = " "
            profile_image_url = " "
            name = " "
            screen_name = " "
            location = " "
            statuses_count = " "
            followers_count = " "
            friends_count = " "
            created_at = " "
            description = " "
            url = " "
            favourites_count = " "
            listed_count = " "
            is_there_default_image = False
            is_there_default_background = False
            # start with the latest day and time
            counter = 0
            for day in sorted(dic[id], reverse = True):
                for time in sorted(dic[id][day], reverse = True):
                    counter += 1
                    if counter <= max_num_tw:
                        candidate_background_image_url = dic[id][day][time]['profile_background_image_url']
                        candidate_image_url = dic[id][day][time]['profile_image_url']
                        if profile_background_image_url == ' ' and candidate_background_image_url != "NA":
                            if re.search(r'abs.twimg.com/images/themes/theme1/bg', candidate_background_image_url):
                                is_there_default_background = True
                            if not re.search(r'abs.twimg.com/images/themes/theme1/bg', candidate_background_image_url):
                                try: 
                                    background_url_check = requests.get(candidate_background_image_url)
                                    if background_url_check.ok:
                                        profile_background_image_url = candidate_background_image_url
                                except:
                                    pass
                        if profile_image_url == " " and candidate_image_url != "NA":
                            if re.search(r'default_profile_images/default_profile', candidate_image_url):
                                is_there_default_image = True
                            if not re.search(r'default_profile_images/default_profile', candidate_image_url):
                                try:
                                    image_url_check = requests.get(candidate_image_url)
                                    if image_url_check.ok:
                                        profile_image_url = candidate_image_url
                                except:
                                    pass
                        if url == " " and dic[id][day][time]['url'] != "NA":
                            url = dic[id][day][time]['url']
                        if location == " " and dic[id][day][time]['location'] != "NA":
                            location = dic[id][day][time]['location']
                        if description == " " and dic[id][day][time]['description'] != "NA": 
                            description = dic[id][day][time]['description']
                        name = dic[id][day][time]['name']
                        screen_name =  dic[id][day][time]['screen_name']
                        statuses_count = dic[id][day][time]['statuses_count']
                        followers_count = dic[id][day][time]['followers_count']
                        friends_count = dic[id][day][time]['friends_count']
                        full_creation_date = datetime.datetime.strptime(dic[id][day][time]['created_at'], '%Y-%m-%d %H:%M:%S')
                        created_at = '{0} {1},  {2}'.format(full_creation_date.strftime("%B"), full_creation_date.strftime("%d"), full_creation_date.strftime("%Y"))
                        favourites_count = dic[id][day][time]['favourites_count']
                        listed_count = dic[id][day][time]['listed_count']
                    if profile_image_url == " " and is_there_default_image:
                        profile_image_url = 'http://abs.twimg.com/sticky/default_profile_images/default_profile_1_normal.png'
                    if profile_background_image_url == " " and is_there_default_background:
                        profile_background_image_url = 'http://abs.twimg.com/images/themes/theme1/bg.png'
            outp = open(path + 'html_id_{0}_screenname_{1}.html'.format(id, screen_name), 'w')
            outp.write('<html><head><style type="text/css"> #left { margin: 0; padding: 0; position: absolute; left: 20; top: 150; width: 50%; } #right { margin: 0; padding: 0; position: absolute; right: 0; top: 150; width: 50%; }  </style> </head> <body bgcolor="#F5F5F5"> <img src="' + profile_background_image_url + '" style="width:30%; height:20%" /> <div id="left"> <table cellspacing="15px"> <tr> <td > <img src="' + profile_image_url + '" width="80" heigth="80"/> </td> </tr> <tr> <td > <font size="5"> <b> ' + str(name) + ' </b> </font> </td> </tr> <tr> <td> <font color="#808080"> @' + str(screen_name) +' </font> </td> </tr> <tr> <td> ' + str(description) +'  </td> </tr> <tr> <td> <img src="https://www.neustar.biz/base/img/icon-locate-big-gry.png" width="15" height="15"/> ' + str(location) + ' </td> </tr> <tr><td> <img src="https://cdn2.iconfinder.com/data/icons/web/512/Link-512.png" width="15" height="15" /> <a href="' + url + '"> ' + url + ' </a> </td></tr><tr><td> <img src="http://iconshow.me/media/images/Mixed/line-icon/png/256/calendar-256.png" width="15" height="15" /> Дата регистрации: ' + str(created_at) + ' </td></tr></table> </div> <div id="right"><table><tr><td align="center" width="15%"> <font color="#808080">Твиты</font> </td> <td align="center" width="15%"> <font color="#808080"> Читаемые </font> </td> <td align="center" width="15%"> <font color="#808080"> Читатели </font> </td> <td align="center" width="15%"> <font color="#808080"> Нравится </font> </td> <td align="center" width="15%"> <font color="#808080"> Списки </font> </td> </tr><tr><td align="center" width="15%"> <font color="#4169E0"> <b>' + str(statuses_count) + '</b> </font>  </td> <td align="center" width="15%">  <font color="#4169E0"> <b>' + str(friends_count) + ' </b></font> </td> <td align="center" width="15%">  <font color="#4169E0"> <b>' + str(followers_count) + '</b></font>  </td> <td align="center" width="15%">  <font color="#4169E0"> <b>' + str(favourites_count) + '</b></font>  </td> <td align="center" width="15%">  <font color="#4169E0"> <b>' + str(listed_count) + '</b></font>  </td> </tr> </table>')
            # write out tweets to html
            counter = 0
            for day in sorted(dic[id], reverse = True):
                for time in sorted(dic[id][day], reverse = True):
                    counter += 1
                    if counter <= max_num_tw:
                        text = dic[id][day][time]['tweet']
                        name = dic[id][day][time]['name']
                        screen_name = dic[id][day][time]['screen_name']
                        tweet_id = dic[id][day][time]['tweet_id']
                        full_time = dic[id][day][time]['full_time']
                        outp.write('<blockquote class="twitter-tweet" width="450"><p> ' + text + '</p> ' + name + " (@" + screen_name + ") <a href='https://twitter.com/" + screen_name + '/status/' + tweet_id + "'>" + full_time + '</a></blockquote>' + " <script src='https://platform.twitter.com/widgets.js' charset='utf-8'></script>" + '\n')
            outp.write('</div> </body> </html>')  
            outp.close()


