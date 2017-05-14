from pysmap import SmappDataset
import datetime, time, re, math
import numpy as np
# added

class Twitter_accounts():
    # 4 - update_tw_per_day
    # 8 - update_languages
    # 9 - update_account_creation_date
    # 14 - make_politicness
    # Politicness monthly (!!!weekly): how many tweets in a given month did we get out of all tweets in that month
    # +Collect data for dataset
    
    def __init__(self, start_date, end_date, account_subset = None):
        '''
        Collections is a list of collections. Dates as yyyy-mm-dd strings
        '''
        # Time-related attributes
        self.start = datetime.date(int(start_date[:4]), int(start_date[5:7]), int(start_date[8:]))
        self.end = datetime.date(int(end_date[:4]), int(end_date[5:7]), int(end_date[8:]))
        self.start_year = time.strptime(start_date, "%Y-%m-%d")[0]
        self.start_month = time.strptime(start_date, "%Y-%m-%d")[1]
        self.end_year = time.strptime(end_date, "%Y-%m-%d")[0]
        self.end_month = time.strptime(end_date, "%Y-%m-%d")[1]
        # Reference to collections and subsets
        self.account_subset = account_subset
        # References to storing sets and dictionaries
        self.feature_dict = {}
        self.days = set()
        self.all_tweet_ids = set()
        self.tw_per_day = {}
        self.tw_per_account = {}
        self.active_days_per_account = {}
        self.id_lang_dict = {}
        self.account_creation_date = {}
        self.min_max_tweets_per_account = {}
        self.user_for_entropy_time_sorted_dict = {}
        # Set time storage for num tweets
        min_month, max_month = self._enumerate_months_()
        self.tw_per_month_per_account = {}
        for month_num in range(min_month,max_month+1):
            self.tw_per_month_per_account[month_num] = {}
        # Set monthly storage for politicness
        self.min_max_tweets_per_account_per_month = {}
    
    
    def _enumerate_months_(self):
        year_dif = self.end_year - self.start_year
        max_month = year_dif*12 + self.end_month
        min_month = self.start_month
        return (min_month, max_month)
    
    
    def loop(self, collections, max_tweets = 'all'):
        '''
        Main function. Iterates over a tweet collection and stores information.
        '''
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
                        # Check if user_id is in the subset of ids provided (if any)
                        if self.account_subset is None or tw['user']['id_str'] in self.account_subset:
                            tw_date_stamp = self.get_tw_date_stamp(tw)
                            self.update_days(tw, tw_date_stamp)
                            self.update_tw_per_account(tw)
                            self.update_tw_per_month_per_account(tw)
                            self.update_languages(tw)
                            self.update_active_days(tw, tw_date_stamp)
                            self.update_account_creation_date(tw)
                            self.update_tw_per_day(tw, tw_date_stamp)
                            self.update_min_max_tweets_per_account(tw)
                            self.update_min_max_tweets_per_account_per_month(tw)
                            self.update_primary_features_dict(tw, tw_date_stamp)
                            self.update_user_for_entropy_time_sorted_dict(tw)
    
    
    def is_in_time_range(self, tw):
        tw_created_list = tw['created_at'].split(' ')
        time_obj = time.strptime('%s %s %s' % (tw_created_list[1], tw_created_list[2], tw_created_list[5]), "%b %d %Y")
        if datetime.date(time_obj[0], time_obj[1], time_obj[2]) >= self.start and datetime.date(time_obj[0], time_obj[1], time_obj[2]) <= self.end:
            return True
        return False
    
    
    def update_days(self, tw, date_stamp):
        self.days.add(date_stamp)
    
    
    def update_tw_per_account(self, tw):
        if tw['user']['id_str'] not in self.tw_per_account:
            self.tw_per_account[tw['user']['id_str']] = 1
        else:
            self.tw_per_account[tw['user']['id_str']] += 1
    
    
    def update_tw_per_month_per_account(self, tw):
        tw_created_list = tw['created_at'].split(' ')
        time_obj = time.strptime('%s %s %s' % (tw_created_list[1], tw_created_list[2], tw_created_list[5]), "%b %d %Y")
        year_dif = time_obj[0] - self.start_year
        current_month_num = year_dif*12 + time_obj[1]
        if tw['user']['id_str'] not in self.tw_per_month_per_account[current_month_num]:
            self.tw_per_month_per_account[current_month_num][tw['user']['id_str']] = 1
        else:
            self.tw_per_month_per_account[current_month_num][tw['user']['id_str']] += 1
    
    
    def update_languages(self, tw):
        if tw['user']['id_str'] not in self.id_lang_dict:
            self.id_lang_dict[tw['user']['id_str']] = {}
            self.id_lang_dict[tw['user']['id_str']]['acc_lang'] = {}
            self.id_lang_dict[tw['user']['id_str']]['tw_lang'] = {}
            #self.id_lang_dict[tw['user']['id_str']]['tw_count'] = 0
        #self.id_lang_dict[tw['user']['id_str']]['tw_count'] += 1
        if tw['user']['lang'] not in self.id_lang_dict[tw['user']['id_str']]['acc_lang']:
            self.id_lang_dict[tw['user']['id_str']]['acc_lang'][tw['user']['lang']] = 1
        else:
            self.id_lang_dict[tw['user']['id_str']]['acc_lang'][tw['user']['lang']] += 1
        if 'lang' in tw:
            if tw['lang'] not in self.id_lang_dict[tw['user']['id_str']]['tw_lang']: # ?
                self.id_lang_dict[tw['user']['id_str']]['tw_lang'][tw['lang']] = 1
            else:
                self.id_lang_dict[tw['user']['id_str']]['tw_lang'][tw['lang']] += 1
    
    
    def update_active_days(self, tw, date_stamp):
        if tw['user']['id_str'] not in self.active_days_per_account:
            self.active_days_per_account[tw['user']['id_str']] = set()
        self.active_days_per_account[tw['user']['id_str']].add(date_stamp)
    
    
    def get_tw_date_stamp(self, tw):
        tw_created_list = tw['created_at'].split(' ')
        time_obj = time.strptime('%s %s %s' % (tw_created_list[1], tw_created_list[2], tw_created_list[5]), "%b %d %Y")
        date_stamp = str(time_obj[0]) + '-' + str(time_obj[1]) + '-' + str(time_obj[2])
        return date_stamp
    
    
    def update_account_creation_date(self, tw):
        tw_created_list = tw['user']['created_at'].split(' ')
        time_obj = time.strptime('%s %s %s' % (tw_created_list[1], tw_created_list[2], tw_created_list[5]), "%b %d %Y")
        date_stamp = str(time_obj[0]) + '-' + str(time_obj[1]) + '-' + str(time_obj[2])
        if tw['user']['id_str'] not in self.account_creation_date:
            self.account_creation_date[tw['user']['id_str']] = date_stamp
    
    
    def update_tw_per_day(self, tw, date_stamp):
        if date_stamp not in self.tw_per_day:
            self.tw_per_day[date_stamp] = 1
        else:
            self.tw_per_day[date_stamp] += 1
    
    
    def get_interface_language_percentages(self, language):
        output = {}
        for account in self.id_lang_dict:
            if language in self.id_lang_dict[account]['acc_lang']:
                output[account] = self.id_lang_dict[account]['acc_lang'][language]/self.tw_per_account[account]*100
            else:
                output[account] = 0
        return output
    
    
    def get_tweet_language_percentages(self, language):
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
        Used to compute politicness
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
    
    
    def make_politicness(self):
        self.politicness = {}
        # Get total number of tweets during data collection
        for el in self.min_max_tweets_per_account:
            if self.min_max_tweets_per_account[el]['total_max'] != self.min_max_tweets_per_account[el]['total_min']:
                self.min_max_tweets_per_account[el]['total_tw'] = self.min_max_tweets_per_account[el]['total_max'] - self.min_max_tweets_per_account[el]['total_min']
            else:
                self.min_max_tweets_per_account[el]['total_tw'] = 'NA'
        # Get politicness
        for el in self.min_max_tweets_per_account:
            if self.min_max_tweets_per_account[el]['total_tw'] != 'NA':
                self.politicness[el] = self.tw_per_account[el] / self.min_max_tweets_per_account[el]['total_tw']
            else:
                self.politicness[el] = 'NA'                    
    
    
    def get_politicness(self):
        politicness = {}
        # Get total number of tweets during data collection
        for el in self.min_max_tweets_per_account:
            if self.min_max_tweets_per_account[el]['total_max'] != self.min_max_tweets_per_account[el]['total_min']:
                self.min_max_tweets_per_account[el]['total_tw'] = self.min_max_tweets_per_account[el]['total_max'] - self.min_max_tweets_per_account[el]['total_min']
            else:
                self.min_max_tweets_per_account[el]['total_tw'] = 'NA'
        # Get politicness
        for el in self.min_max_tweets_per_account:
            if self.min_max_tweets_per_account[el]['total_tw'] != 'NA':
                politicness[el] = self.tw_per_account[el] / self.min_max_tweets_per_account[el]['total_tw']
            else:
                politicness[el] = 'NA'
        return politicness

    
    def update_min_max_tweets_per_account_per_month(self, tw):
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
    
    
    def make_politicness_per_account_per_month(self):
        self.politicness_per_account_per_month = {}
        # Get total number of tweets per month
        for acc in self.min_max_tweets_per_account_per_month:
            self.politicness_per_account_per_month[acc] = {}
            for month in self.min_max_tweets_per_account_per_month[acc]:
                if self.min_max_tweets_per_account_per_month[acc][month]['time_n'] != 'NA':
                    self.min_max_tweets_per_account_per_month[acc][month]['total_tw'] = self.min_max_tweets_per_account_per_month[acc][month]['time_n_numtw'] - self.min_max_tweets_per_account_per_month[acc][month]['time_1_numtw']
                    self.min_max_tweets_per_account_per_month[acc][month]['num_days'] = self.min_max_tweets_per_account_per_month[acc][month]['time_n'][2] - self.min_max_tweets_per_account_per_month[acc][month]['time_1'][2]
                    if self.min_max_tweets_per_account_per_month[acc][month]['num_days'] > 15:
                        if self.min_max_tweets_per_account_per_month[acc][month]['total_tw'] != 0:
                            self.politicness_per_account_per_month[acc][month] = self.tw_per_month_per_account[month][str(acc)] / self.min_max_tweets_per_account_per_month[acc][month]['total_tw']
                        else:
                            self.politicness_per_account_per_month[acc][month] = 'NA'
                    else:
                        self.politicness_per_account_per_month[acc][month] = 'UR'
                else:
                    self.politicness_per_account_per_month[acc][month] = 'NA'
    
    
    def get_politicness_per_account_per_month(self):
        politicness_per_account_per_month = {}
        # Get total number of tweets per month
        for acc in self.min_max_tweets_per_account_per_month:
            politicness_per_account_per_month[acc] = {}
            for month in self.min_max_tweets_per_account_per_month[acc]:
                if self.min_max_tweets_per_account_per_month[acc][month]['time_n'] != 'NA':
                    self.min_max_tweets_per_account_per_month[acc][month]['total_tw'] = self.min_max_tweets_per_account_per_month[acc][month]['time_n_numtw'] - self.min_max_tweets_per_account_per_month[acc][month]['time_1_numtw']
                    self.min_max_tweets_per_account_per_month[acc][month]['num_days'] = self.min_max_tweets_per_account_per_month[acc][month]['time_n'][2] - self.min_max_tweets_per_account_per_month[acc][month]['time_1'][2]
                    if self.min_max_tweets_per_account_per_month[acc][month]['num_days'] > 15:
                        if self.min_max_tweets_per_account_per_month[acc][month]['total_tw'] != 0:
                            politicness_per_account_per_month[acc][month] = self.tw_per_month_per_account[month][str(acc)] / self.min_max_tweets_per_account_per_month[acc][month]['total_tw']
                        else:
                            politicness_per_account_per_month[acc][month] = 'NA'
                    else:
                        politicness_per_account_per_month[acc][month] = 'UR'
                else:
                    politicness_per_account_per_month[acc][month] = 'NA'
        return politicness_per_account_per_month
    
    
    def update_primary_features_dict(self, tw, date_stamp):
        def is_retweet(tweet):
            '''
            Takes a python-native tweet object (a dict). Returns True if a tweet is any kind of retweet
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
    
    
        def is_there_number_except_year(screen_name): 
            '''
            Used in make_primary_features() to analyze user sceen_name. 
            '''
            if re.search(r'[0-9]+', screen_name):
                if not int(screen_name[re.search(r'[0-9]+', screen_name).start():re.search(r'[0-9]+', screen_name).end()]) >= 50 or not int(screen_name[re.search(r'[0-9]+', screen_name).start():re.search(r'[0-9]+', screen_name).end()]) <= 99:
                    return True
            return False
    
    
        def is_there_more_than_1_word(name):
            '''
            Used in make_primary_features() to analyze user name. 
            '''
            if re.search(r' ', name):
                return True
            return False
        
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
            if is_retweet(tw):
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
            if is_there_number_except_year(tw['user']['screen_name']):
                self.feature_dict[user_id]['digits_in_screen_name'] = 1    
            else:
                self.feature_dict[user_id]['digits_in_screen_name'] = 0
            if 'location' in tw['user'] and not tw['user']['location'] is None:
                if len(tw['user']['location']) > 0:
                    self.feature_dict[user_id]['location_specified'] = 1
            else:
                self.feature_dict[user_id]['location_specified'] = 0
            if is_there_more_than_1_word(tw['user']['name']):
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
            if is_retweet(tw):
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
            if is_there_number_except_year(tw['user']['screen_name']):
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
        Returns a dictionary with probs of pauses ...
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
        Returns a dictionary with id_str as key and value = [entropy, number of DIFFERENT pauses ]
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
        self.final_feature_dict = {}
        if not hasattr(self, 'entropy'):
            self.make_entropy()
        if not hasattr(self, 'politicness'):
            self.make_politicness()
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
            if self.politicness[id] == 'NA':
                self.final_feature_dict[id]['politicness'] = 0
            elif self.politicness[id] >= 1:
                self.final_feature_dict[id]['politicness'] = 1
            else: 
                self.final_feature_dict[id]['politicness'] = self.politicness[id]
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
            self.final_feature_dict[id]['max_num_tweets_this_user_favored_over_total_tweets'] = np.max(self.feature_dict[id]['favourites_count']) / self.feature_dict[id]['total_tw_count']
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
        output = {}
        for acc in selfdict:
            if acc in subset:
                output[acc] = selfdict[acc]
        return output



