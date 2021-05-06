#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split
from deepctr.models import DeepFM
import deepctr.feature_column
from deepctr.feature_column import SparseFeat, DenseFeat
import ast
from pickle import load
import keras
import numpy as np
from deepctr.layers import custom_objects
import sys
from constants import (
    SPARSE_FEATURES,
    DENSE_FEATURES,
    TARGET

)


# In[ ]:


user = sys.argv[1]
# just using inital list of all followed feeds, this is not advised for production model
feeds = list(UserSubscription.objects.order_by().values_list('feed_id', flat=True).distinct())
assert type(feeds) == list()
rec_num = 10
followed_feeds = list(UserSubscription.objects.filter(user=user).values('feed_id')) 
#feeds = list(UserSubscription.objects.filter(user=user).values('feed_id'))

possible_recommendations = set(total_feeds) - set(feeds)

active_subs = [Feed.objects.get(pk=x).active_subscribers for x in possible_recommendations]
premium_subs = [Feed.objects.get(pk=x).premium_subscribers for x in possible_recommendations]
num_subs = [Feed.objects.get(pk=x).num_subscribers for x in possible_recommendations]
average_stories_per_month = [Feed.objects.get(pk=x).average_stories_per_month for x in possible_recommendations]
user = [self.user_id]*(len(possible_recommendations)+1)
is_premium = Profile.objects.get(user_id=user).is_premium
# not sure how this comes in, will have to check it out on server
score_data = [Feed.get_by_id(x).well_read_score() for x in possible_recommendations]

 # pretty sure its a dict
temp = pd.DataFrame(score_data)
        
active_premium_subscribers = [Feed.objects.get(pk=x).active_premium_subscribers for x in possible_recommendations]
user_shared_stories_count = MSharedStory.objects.filter(user_id=self.user).count()
        
# total shares_per_feed might be the same as share_count
total_shares_per_feed = [MSharedStory.objects.filter(story_feed_id=x).count() for x in possible_recommendations]


# In[ ]:


# create our full input dataframe
input_df = pd.DataFrame(columns=SPARSE_FEATURES + DENSE_FEATURES)
input_df['read_pct'],input_df['reader_count'],input_df['reach_score'] = temp['read_pct'],temp['reader_count'],temp['reach_score']
input_df['story_count'],input_df['share_count'] = temp['story_count'],temp['share_count']
del temp
input_df['active'] = [Feed.objects.get(pk=x).active for x in possible_recommendations]
input_df['active_subs'],input_df['num_subs'],input_df['premium_subs'] = active_subs,num_subs,premium_subs
input_df['average_stories_per_month'],input_df['user'],input_df['feed_id'] =average_stories_per_month,user,possible_recommendations
input_df['is_premium'] = [is_premium] * (len(possible_recommendations)+1)
input_df['active_premium_subscribers'] = active_premium_subscribers
input_df['user_shared_stories_count'] = [user_shared_stories_count] * len((possible_recommendations)+1)
input_df['total_shares_per_feed'] = total_shares_per_feed
### should be all the current fields

assert input_df.columns == SPARSE_FEATURES + DENSE_FEATURES


# In[ ]:


# normalize data
# this must be done
# no need anymore for reading/writing vocab sizes to file, figured it out
vocabs = {}
for feat in SPARSE_FEATURES:
        # need a labelEncoder for each feature
        lbe = load(open( feat + '-' + 'lbe.pkl', 'rb'))
        input_df[feat] = lbe.transform(input_df[feat])
        vocabs[feat] = len(lbe.classes_)
        
mms = MinMaxScaler(feature_range=(0,1))
# shouldn't need to save and load a ranged numerical features model like minmaxscaler
#mms = load(open('minmax.pkl', 'rb'))
input_df[DENSE_FEATURES] = mms.transform(input_df[DENSE_FEATURES])


# In[ ]:


fixlen_feature_columns = [SparseFeat(feat, vocabulary_size=vocabs[feat],embedding_dim=16)
                       for i,feat in enumerate(SPARSE_FEATURES)] + [DenseFeat(feat, 1,)
                      for feat in DENSE_FEATURES]


# In[ ]:


linear_feature_columns = fixlen_feature_columns
dnn_feature_columns = fixlen_feature_columns


# In[ ]:


feature_names = deepctr.feature_column.get_feature_names(linear_feature_columns + dnn_feature_columns)


# In[ ]:


test_model_input = {name:input_df[name] for name in feature_names}
del input_df


# In[ ]:


model = keras.models.load_model('model.keras', custom_objects)


# In[ ]:


pred_ans = model.predict(test_model_input, batch_size=256)


# In[ ]:


# convert predictions to a little bit better format
predictions = [i[0] for i in pred_ans]


# In[ ]:


# feeds = input_df['feed_id'].tolist()


# In[ ]:


# lets sort our predictions from highest to lowest
results = sorted(dict(zip(feeds, predictions)).items(),  key=lambda x: x[1], reverse=True)


# In[ ]:


# lets grab the top x amount of feeds
self.feed_recommendations = results[:rec_num]
