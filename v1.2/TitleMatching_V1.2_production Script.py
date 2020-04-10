
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 16:24:56 2020

@author: gbapat
"""
                    # *************************************Section 1*******************************************#

from fuzzywuzzy import fuzz
import pandas as pd
import numpy as np
import re
from datetime import datetime

    
input_data = pd.read_csv(r"Input file path", encoding='latin-1')  

# 1.1 Lowercase the entire dataframe
input_data= input_data.applymap(lambda s:s.lower() if type(s) == str else s)

# 1.2 Assigning reported title episode name and canonical title episode name to two new variable as u_name and m_name will be normalized
input_data['u_epname']=input_data['u_name']
input_data['m_epname']=input_data['m_name']

# 1.3 Filtering manual matched titles coming from 'Digital' source with entity subtype as 'tv_episode'

dig_tv_manual_data=input_data[(input_data['u_original_source_name']=="digital") & (input_data['u_entity_subtype_name']=="tv_episode") & (input_data['is_automatch']=="f")]

dig_tv_manual_data.u_entity_id.nunique()

# 1.4 Normalising 'u_name', 'm_name', 'u_proto_name', 'm_proto_name' with following conditions:
# Converting to lower case
# Removing spaces and other special characters

normalized=['u_name','m_name','u_proto_name', 'm_proto_name']
for i in normalized:
    dig_tv_manual_data[i]=dig_tv_manual_data[i].str.replace(' and ', '')
    dig_tv_manual_data[i]=dig_tv_manual_data[i].str.replace(r'and|\W|_', '')
    dig_tv_manual_data[i]=dig_tv_manual_data[i].str.replace('[^a-zA-Z0-9]', '')
dig_tv_manual_data['m_episode_number'] = pd.to_numeric(dig_tv_manual_data['m_episode_number'].str.replace(r'[^\d%]',''))

# 1.5 Filtering out numeric titles and changing data type of certain fields

ep_season=['u_episode_number','u_season_number','m_episode_number', 'm_season_number']
for j in ep_season:
    dig_tv_manual_data[j]=dig_tv_manual_data[j].fillna(0).astype(np.int64)
    
dig_tv_manual_data["u_episode_number"]=np.where(dig_tv_manual_data["u_episode_number"]==0,111111,dig_tv_manual_data["u_episode_number"])
dig_tv_manual_data["u_season_number"]=np.where(dig_tv_manual_data["u_season_number"]==0,111111,dig_tv_manual_data["u_season_number"])
dig_tv_manual_data["m_episode_number"]=np.where(dig_tv_manual_data["m_episode_number"]==0,222222,dig_tv_manual_data["m_episode_number"])
dig_tv_manual_data["m_season_number"]=np.where(dig_tv_manual_data["m_season_number"]==0,222222,dig_tv_manual_data["m_season_number"])

dig_tv_manual_data=dig_tv_manual_data[~dig_tv_manual_data['u_name'].astype(str).str.isnumeric()]


                   # *************************************Section 2*******************************************#

    
# 2.1 Creating lists from metadata

#name_ratio - Fuzzy ratio for episode name
name_ratio = []
#proto_ratio - Fuzzy ratio for proto name
proto_ratio = []
#Creating lists to store the matching status of metadata(TRUE or FALSE)
name_status=[]
proto_name_status=[]
ep_match=[]
season_match=[]
n_status=[]
logic=[]
key=[]

# 2.2 Identifying patterns and changing u_name, metadata comparison, fuzzy calculation

# Below lines of codes checks whether the reported title's metadata (episode name, proto name, episode number and season number) are  an exact match or not, with the canonical title's metadata and update the status ('TRUE - exact matched', 'False - not exact matched') in the main table and also calculate fuzzy score between  episode name and proto name of reported titles and canonical titles

for (x_name, y_name, x_proto, y_proto,x_epno,y_epno,x_sno,y_sno,x_epname,y_epname) in zip(dig_tv_manual_data['u_name'], dig_tv_manual_data['m_name'],dig_tv_manual_data['u_proto_name'],dig_tv_manual_data['m_proto_name'],dig_tv_manual_data['u_episode_number'],dig_tv_manual_data['m_episode_number'],dig_tv_manual_data['u_season_number'],dig_tv_manual_data['m_season_number'],dig_tv_manual_data['u_epname'],dig_tv_manual_data['m_epname']):
    
    if str(x_name)==str(y_name):
        temp_name_status="TRUE"
    else:
        temp_name_status="FALSE"
        
    if str(x_proto)==str(y_proto):
        temp_proto_name_status="TRUE"
    else:
        temp_proto_name_status="FALSE"
            
    if str(x_epno)==str(y_epno):
         temp_epno_status="TRUE"
    else:
         temp_epno_status="FALSE"
         
    if str(x_sno)==str(y_sno):
        temp_sno_status="TRUE"
    else:
        temp_sno_status="FALSE" 
        
    key_value=temp_name_status[0]+temp_proto_name_status[0]+temp_epno_status[0]+temp_sno_status[0]
           
#Appending matching status to newly created list         
           
    name_status.append(temp_name_status)  
    proto_name_status.append(temp_proto_name_status)
    ep_match.append(temp_epno_status)
    season_match.append(temp_sno_status)
    
#Calculate'Fuzzy ratio'  
    
    temp_name_ratio = fuzz.ratio(str(x_name),str(y_name))
    name_ratio.append(temp_name_ratio)
    temp_proto_name_ratio = fuzz.ratio(str(x_proto),str(y_proto))
    proto_ratio.append(temp_proto_name_ratio)
    key.append(key_value)
    
#Identifying titles that follow patterns and changing respective u_name's.
    
    #Extracting string from the title and comparing u_name,m_name
    if re.match("episode([0-9]+)([a-zA-Z]+)",x_name):
        r=re.match("episode([0-9]+)([a-zA-Z]+)",x_name)
        t_name=r.group(2)
        if str(t_name)==str(y_name) and str(x_proto)==str(y_proto) and str(x_epno)==str(y_epno) and str(x_sno)==str(y_sno):
            t_n_status, t_logic="accepted","logic 1"
        else:
            t_n_status, t_logic="rejected","logic 1"
    #verifying the number of digits in the string    
    elif re.match("episode([0-9]+)$",x_name):
        r=re.match("episode([0-9]+)$",x_name)
        t_name=r.group(1)
        
        d = sum(elem.isdigit() for elem in t_name)
        if d==1:
            t_name= str(x_sno)+'0'+str(x_epno)
        elif d==2:
            t_name= str(x_sno)+str(x_epno)
        elif d==3:
            t_name=t_name
        if str(t_name)==str(y_name) and str(x_proto)==str(y_proto):
            t_n_status, t_logic="accepted","logic 1"          
        else:
            t_n_status, t_logic="rejected","logic 1"
    #Swapping the position of the words in the title to match with canonical title
    elif re.match("([a-zA-Z0-9^' a-zA-Z0-9]+, The)",y_epname) and re.match("(The [a-zA-Z0-9]+)",x_epname):
        split_name=y_epname.split(",")
        nosp_name=re.sub('[^A-Za-z0-9]+', '', split_name)
        t_name=nosp_name
        if str(x_name)==str(t_name) and str(x_proto)==str(y_proto):
            t_n_status, t_logic="accepted","logic 3"          
        else:
            t_n_status, t_logic="rejected","logic 3"
    #Removing Sub and Dub from the titles        
    elif re.match("Sub |Dub ",x_epname):
        Sub = re.sub(r"Sub |Dub ", "", x_epname)
        x_epname=Sub
        x_name=x_epname
        s1=x_name
        s3=s1.replace(' ', '')
        s4=s3.replace('[^a-zA-Z0-9]', '')
        t_name=s4
        if str(t_name)==str(y_name) and str(x_proto)==str(y_proto):
            t_n_status, t_logic="accepted","logic 4"          
        else:
            t_n_status, t_logic="rejected","logic 4"
    #Remove "No" from the reported title and match with canonical title    
    elif re.match("Live Pd Police",x_epname):
        Sub1 = re.sub(r'\bNo\b\s+',"",x_epname)
        x_epname=Sub1
        x_name=x_epname
        s1=x_name
        s3=s1.replace(' ', '')
        s4=s3.replace('[^a-zA-Z0-9]', '')
        t_name=s4
        if str(t_name)==str(y_name) and str(x_proto)==str(y_proto):
            t_n_status, t_logic="accepted","logic 6"    
        else:
            t_n_status, t_logic="rejected","logic 6"
    #Extract date from reported title and match with canonical title
    elif re.search('(watchwhathappenslive\d{2}\d{2}\d{4})', x_name):
       
        match = re.search('(watchwhathappenslive\d{2}\d{2}\d{4})', x_name)
        match = re.search('\d{2}\d{2}\d{4}', match.group())
        strDate=match.group()
        objDate = datetime.strptime(strDate, '%m%d%Y')
        t_name=datetime.strftime(objDate, '%m%d%Y')
        if str(t_name)==str(y_name) and str(x_proto)==str(y_proto):
            t_n_status, t_logic="accepted","logic 7"    
        else:
            t_n_status, t_logic="rejected","logic 7"
    #Convert reported title to mmddyyyy format and match with canonical title
    elif re.search('([mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday]+\d{2}\d{2}\d{4})', x_name):
        match = re.search('([mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday]+\d{2}\d{2}\d{4})', x_name)
        match = re.search('\d{2}\d{2}\d{4}', match.group())
        t_name=match.group()
        if str(t_name)==str(y_name) and str(x_proto)==str(y_proto):
            t_n_status, t_logic="accepted","logic 8"      
        else:
            t_n_status, t_logic="rejected","logic 8"
    #Extract date from reported title and match with canonical title    
    elif re.search('(\d{2}\d{2}\d{4}[a-zA-Z0-9])', x_name):
        m=re.search('(\d{2}\d{2}\d{4})', x_name)
        t_name=m.group()
        if str(t_name)==str(y_name) and str(x_proto)==str(y_proto):
            t_n_status, t_logic="accepted","logic 9"     
        else:
            t_n_status, t_logic="rejected","logic 9"
    else: 
        t_n_status,t_logic="rejected", "No logic identified"
       
    logic.append(t_logic)  
    n_status.append(t_n_status)

# 2.3 Creating dataframe for each list and appending to make a single frame

name_frame=pd.DataFrame(name_status,columns =['name_status'])
name_ratioframe=pd.DataFrame(name_ratio,columns =['name_ratio'])
proto_ratioframe=pd.DataFrame(proto_ratio,columns =['proto_name_ratio'])
proto_frame=pd.DataFrame(proto_name_status,columns =['proto_name_status'])
episode_frame=pd.DataFrame(ep_match,columns =['ep_match'])
season_frame=pd.DataFrame(season_match,columns =['season_match'])
n_staus_frame=pd.DataFrame(n_status,columns =['n_status'])
logic_frame=pd.DataFrame(logic,columns =['logic'])
key_frame=pd.DataFrame(key,columns =['key'])
appendedframe=pd.concat([name_ratioframe,proto_ratioframe,name_frame,proto_frame,episode_frame,season_frame,n_staus_frame, logic_frame, key_frame], axis=1)

# 2.4 Reset the index of the DataFrames
appendedframe.reset_index(drop=True, inplace=True)
dig_tv_manual_data.reset_index(drop=True, inplace=True)
dig_tv_manual_data=pd.concat([dig_tv_manual_data,appendedframe], axis=1 ,sort=False)


                  # *************************************Section 3*******************************************#

# 3.1 Logic Box

#Logic Box
logic_box = {'key':["TTTT", "TTTF", "TTFT", "TTFF","TFTT", "FTTT", "TFTF", "TFFT", "TFFF", "FTTF", "FTFT" ,"FTFF", "FFTT", "FFTF","FFFT", "FFFF"],
    'level': ["L1", "L2", "L3", "L4", "L5", "L9", "L6", "L7","L8","L10", "L11", "L12", "L13", "L14", "L15", "L16"],
    'priority':[1, 2, 3, 4, 5, 9, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16],
    'threshold':[100,100,100,100,55,80,55,55,55,80,80,80,95,95,95,95]}
logic_box = pd.DataFrame(logic_box)    
dig_tv_manual_data=pd.merge(dig_tv_manual_data, logic_box, on ='key', how='left')
dig_tv_manual_data.u_entity_id.nunique()


                 #  *************************************Section 4*******************************************#


# 4.1 Basic matches

accepted=dig_tv_manual_data
accepted=accepted.sort_values(['u_entity_id', 'priority',], ascending=[1,1])
accepted.u_entity_id.nunique()

variables= {'u_name': 'first','u_episode_number': 'first','u_season_number': 'first','u_original_source_name': 'first','u_entity_type_name': 'first','u_entity_subtype_name': 'first','u_entity_type_id': 'first','u_entity_subtype_id': 'first','u_theatrical_release_date': 'first','u_tv_release_date': 'first','u_unique_series_name': 'first','u_proto_name': 'first','u_directors': 'first','m_entity_id': 'first','m_name': 'first','m_episode_number': 'first','m_season_number': 'first','m_original_source_name': 'first','m_entity_type_name': 'first','m_entity_subtype_name': 'first','m_entity_type_id': 'first','m_entity_subtype_id': 'first','m_theatrical_release_date': 'first','m_tv_release_date': 'first','m_unique_series_name': 'first','m_proto_name': 'first','m_directors': 'first','aggregated_score': 'first','status': 'first','moment_matched': 'first','is_automatch': 'first','u_epname': 'first','m_epname': 'first','name_ratio': 'first','proto_name_ratio': 'first','name_status': 'first','proto_name_status': 'first','ep_match': 'first','season_match': 'first','n_status': 'first','logic': 'first','key': 'first','level': 'first', 'priority':'min'}

#group dataframe
accepted_min=accepted.groupby(["u_entity_id"], as_index=False).agg(variables)
accepted_min["n_status"]=np.where((accepted_min['priority'].isin([1,2,3,4])),"accepted","rejected")             

BAM=accepted_min[accepted_min["n_status"]=="accepted"]
BAM.u_entity_id.nunique()

#Merging sorted dataset and grouped data to create a dataset with all titles and it suggestions with n_status field to show accept/reject
basic=dig_tv_manual_data[dig_tv_manual_data.u_entity_id.isin(BAM["u_entity_id"]) ]
basic = pd.merge(basic, BAM[['u_entity_id','m_entity_id','priority',"n_status"]], how='left', on=['u_entity_id','m_entity_id', 'priority',])
basic["n_status_y"].fillna("rejected" , inplace=True)
basic["n_status_x"]=basic["n_status_y"]
basic.n_status_x.unique()
basic.drop('n_status_y', axis=1, inplace=True)
basic.rename(columns={'n_status_x': 'n_status'},inplace=True)
basic["BAM_status"]="BAM"
basic["logic"]="BAM"
basic.u_entity_id.nunique()

dig_tv_manual_data["BAM_status"]=np.where((dig_tv_manual_data.u_entity_id.isin(basic["u_entity_id"])),"BAM","Not BAM")

# 4.2 Patterns

#titles matched by pattern
patterns_accepted=dig_tv_manual_data[dig_tv_manual_data['n_status']=="accepted"]
patterns_accepted=patterns_accepted[~patterns_accepted.u_entity_id.isin(basic["u_entity_id"])]
patterns=dig_tv_manual_data[dig_tv_manual_data.u_entity_id.isin(patterns_accepted["u_entity_id"])]

# 4.3 Fuzzy

#titles for fuzzy match
dig_tv_manual=dig_tv_manual_data[~dig_tv_manual_data.u_entity_id.isin(basic["u_entity_id"])]
sort_digtv_data= dig_tv_manual[~dig_tv_manual.u_entity_id.isin(patterns_accepted['u_entity_id'])]

#Sort 'the digital_tv_manual_data' on 'u_entity_id' and 'priority' variable
sort_digtv_data=sort_digtv_data.sort_values(['u_entity_id', 'priority',], ascending=[1,1])

fuzzy=sort_digtv_data.groupby(["u_entity_id"], as_index=False).agg(variables)

# Fuzzy Threshold
fuzzy["n_status"]=np.where((fuzzy['priority'].isin([1,2,3,4])),"accepted",
                np.where(((fuzzy['priority']==5) & (fuzzy['proto_name_ratio']>=55)),"accepted",
                np.where(((fuzzy['priority']==6) & (fuzzy['proto_name_ratio']>=55)),"accepted",
                np.where(((fuzzy['priority']==7) & (fuzzy['proto_name_ratio']>=55)),"accepted",
                np.where(((fuzzy['priority']==8) & (fuzzy['proto_name_ratio']>=55)),"accepted",
                                  
                np.where(((fuzzy['priority']==9) & (fuzzy['name_ratio']>=80)),"accepted",
                np.where(((fuzzy['priority']==10) & (fuzzy['name_ratio']>=80)),"accepted",
                np.where(((fuzzy['priority']==11) & (fuzzy['name_ratio']>=80)),"accepted",
                np.where(((fuzzy['priority']==12) & (fuzzy['name_ratio']>=80)),"accepted",
                
                np.where(((fuzzy['priority'].isin([13,14,15,16])) & (fuzzy['name_ratio']>=95) & (fuzzy["proto_name_ratio"]>=90)),"accepted","rejected"))))))))))

#Merging sorted dataset and grouped data to create a dataset with all titles and it suggestions with n_status field to show accept/reject
fuzzy_titles = pd.merge(sort_digtv_data, fuzzy[['u_entity_id','m_entity_id','priority',"n_status"]], how='left', on=['u_entity_id','m_entity_id', 'priority',])

#Assigning "rejected" value to n_status field for titles that has missing values in n_status field.

fuzzy_titles["n_status_y"].fillna("rejected" , inplace=True)
fuzzy_titles["n_status_x"]=fuzzy_titles["n_status_y"]
fuzzy_titles.n_status_x.unique()
fuzzy_titles.drop('n_status_y', axis=1, inplace=True)
fuzzy_titles.rename(columns={'n_status_x': 'n_status'},inplace=True)

                  # *************************************Section 5*******************************************#

# 5.1 Exporting output to csv

all_titles=pd.concat([basic,patterns,fuzzy_titles],axis=0)

all_titles.drop(['name_ratio', 'proto_name_ratio','name_status','proto_name_status','ep_match','season_match','logic','key','level','priority','threshold','BAM_status'],axis = 1, inplace=True)

all_titles.to_csv(r"Output file path")



