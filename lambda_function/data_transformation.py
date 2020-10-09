import pandas as pd
def data_transformation(NewYork_Data,JohnHope_Data):
  #filtering Remove non-US data from the Johns Hopkins dataset.
  JohnHope_Data = JohnHope_Data[JohnHope_Data['Country/Region']=='US'].drop(columns='Country/Region')
  JohnHope_Data.columns = ['date','recovered']

  #cleaning - The date field should be converted to a date object, not a string.
  NewYork_Data['date']  = pd.to_datetime(NewYork_Data['date'],format='%Y-%m-%d')
  JohnHope_Data['date'] = pd.to_datetime(JohnHope_Data['date'],format='%Y-%m-%d')

  #set index
  NewYork_Data.set_index('date', inplace=True)
  JohnHope_Data.set_index('date',inplace=True)

  JohnHope_Data['recovered'] = JohnHope_Data['recovered'].astype('int64')

  Joined_Data = NewYork_Data.join(JohnHope_Data, how='inner')
  Joined_Data.reset_index(inplace=True)

  return Joined_Data
