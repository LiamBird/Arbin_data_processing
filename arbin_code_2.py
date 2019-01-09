## Process code for Arbin data
## Works using text file with raw output from Arbin in format:

## Cycle_Index      Current (A)      Charge capacity (Ah/kg)         Discharge capacity (Ah/kg)     Voltage (V)          

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
np.set_printoptions(formatter={'float': lambda x: "{0:0.2f}".format(x)})

## INPUTS --------------------------------------------------------------------------------------------------------------------
## Enter path and filename
## Enter filename WITHOUT file extension
## Ensure path has format: path = r'<path>' (i.e. preceded by r, with single quotes)
path = r'C:\Users\laure\Dropbox\DATA\Process_code'
filename = 'Arbin_data_1'
## ---------------------------------------------------------------------------------------------------------------------------

## Importing data from text file
f = path+'\\'+filename+'.txt'                       # Sticks together path, filename, and file extension
data = np.asarray(pd.read_csv(f, sep='\t'))         # Imports the data as a numpy array for later processing
data = np.delete(data, (0), 0)                      # Deletes the first imported row (i.e. headers). Can be removed if no headers in text file. 

cycles = int(np.max(data[:, 0]))                    # Finds the maximum value in the cycles column (i.e. the total number of cycles)

## Capacity data from Arbin is cumulative, and charge and discharge data for each cycle have the same 'Cycle index'
## The charge and discharge data from each cycle need to be separated.
## The absolute charge/ discharge values need to be found by subtracting the sum of the previous charge/ discharge values.
## Setting up two arrays to contain the charge/ discharge data:
## (the arrays are initiated filled with 'NaN' such that the row references in the charge/ discharge arrays correspond exactly to the raw data)
cumulat_charge = np.full(data.shape, np.nan, dtype=float)
cumulat_discharge = np.full(data.shape, np.nan, dtype=float)

## Separating the imported data into charge and discharge data.
## The current values are stored in column 1 of data:
## When the current is positive, this is the CHARGE part of the cycle
## When the current is negative, this is the DISCHARGE part of the cycle
for i in range(data.shape[0]):
    if np.sign(data[i, 1]) > 0:
        cumulat_charge[i, :] = data[i, :]
    else:
        cumulat_discharge[i, :] = data[i, :]

## To find the absolute charge/ discharge values, the cumulative charge/ discharge value from the previous cycle needs to be subtracted from each charge/ discharge raw datum after the first.
## The format of the data will be (eg):
##
## 12    -0.05   130    450     1.3     <-- i-2
## 12    -0.05   130    440     1.2     <-- i-1
## 12    -0.05   130    430     1.1     <-- i
## nan   nan     nan    nan     nan     <-- i+1
## nan   nan     nan    nan     nan     <-- i+2
##
## To identify the end of cycle 12, the code looks for i where the values in i=/=nan, but the values in i+1=nan
## Sometimes, spurious single lines with opposite signed current appear: the extra condition to check i-1=/=nan ensures that spurious lines are not recorded
        
end_charge = []                                 # Setting up list to contain row numbers at the end of charge data sets
for i in range(cumulat_charge.shape[0]-1):
    if np.isnan(cumulat_charge[i][2]) == False and np.isnan(cumulat_charge[i-1][2]) == False and np.isnan(cumulat_charge[i+1][2])==True:
        end_charge.append(i)

end_discharge = []                                 # Setting up list to contain row numbers at the end of discharge data sets
for i in range(cumulat_discharge.shape[0]):
    if np.isnan(cumulat_discharge[i][2]) == False and np.isnan(cumulat_discharge[i-1][2]) == False and np.isnan(cumulat_discharge[i+1][2])==True and np.isnan(cumulat_discharge[i+2][2]) == True :
        end_discharge.append(i)

num_cyc = np.min([len(end_charge), len(end_discharge)])

charge_length = np.zeros(shape=(len(end_charge), 1), dtype=int)
for i in range(num_cyc):
    charge_length[i, 0] = end_charge[i] - end_discharge[i]       # Finds the number of rows in each charging data set
# charge_length = np.delete(charge_length, (0), 0)                # Deletes the zeros at the beginning of the matrix
longest_charge = int(np.max(charge_length))                     # Finds the charging data set with the most rows


discharge_length = np.zeros(shape=(len(end_charge), 1), dtype=int)
for i in range(1, num_cyc):
    discharge_length[0] = end_discharge[0]
    discharge_length[i, 0] = end_discharge[i] - end_charge[i-1]  # Finds the number of rows in each discharging data set
# discharge_length = np.delete(discharge_length, (0), 0)              # Deletes the zeros at the beginning of the matrix
longest_discharge = int(np.max(discharge_length))                   # Finds the charging data set with the most rows

## Finding the cumulative charge values to subtract to obtain the absolute charge values
## The 'end_(dis)charge' lists contain the indices for the cumulative (dis)charge capacity at the end of each cycle
## sub_charge and sub_discharge then contain the values of the cumulative (dis)charge capacities ready for subtration from the raw data
sub_charge = [0]
for i in range(len(end_charge)):
    sub_charge.append(float(cumulat_charge[end_charge[i], 2]))

sub_discharge = [0]
for i in range(len(end_discharge)):
    sub_discharge.append(float(cumulat_discharge[end_discharge[i], 3]))

## Magic happens        
charge = np.full((longest_charge, cycles), np.nan)
discharge = np.full((longest_discharge, cycles), np.nan)

for j in range(num_cyc):
    charge[0:charge_length[j][0], j] = cumulat_charge[end_discharge[j]:end_charge[j], 2]-sub_charge[j]
charge = np.delete(charge, (0), 0)

for j in range(1, num_cyc):
    discharge[0:discharge_length[0][0], 0] = cumulat_discharge[0:end_discharge[0], 3]-sub_discharge[0]
    discharge[0:discharge_length[j][0], j] = cumulat_discharge[end_charge[j-1]:end_discharge[j], 3]-sub_discharge[j]

cap_cyc_charge=np.zeros(shape=(charge.shape[1]-1, 2), dtype=float)
for j in range(charge.shape[1]-1):
    cap_cyc_charge[j, 0] = j
    cap_cyc_charge[j, 1] = np.nanmax(charge[:, j])

cap_cyc_discharge=np.zeros(shape=(discharge.shape[1]-1, 2), dtype=float)
for j in range(discharge.shape[1]-1):
    cap_cyc_discharge[j, 0] = j
    cap_cyc_discharge[j, 1] = np.nanmax(discharge[:, j])
    
capvolt_charge = filename+'_capvolt_charge.csv'
capvolt_discharge = filename+'_capvolt_discharge.csv'
capcycles_charge = filename+'_capcycles_charge.csv'
capcycles_discharge = filename+'_capcycles_discharge.csv'

np.savetxt(capvolt_charge, charge, delimiter=',', fmt='%5s')
np.savetxt(capvolt_discharge, discharge, delimiter=',', fmt='%5s')
np.savetxt(capcycles_charge, cap_cyc_charge, delimiter=',', fmt='%5s')
np.savetxt(capcycles_discharge, cap_cyc_discharge, delimiter=',', fmt='%5s')



