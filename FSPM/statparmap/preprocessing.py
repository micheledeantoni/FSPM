import pandas as pd
from scipy.ndimage import gaussian_filter
from mplsoccer import Pitch, VerticalPitch, FontManager, Sbopen
import numpy as np


def preprocess_df(df, binsize = (35,35)):
    pitch = Pitch(pitch_type='opta')
    bin_statistic = pitch.bin_statistic(df.x, df.y, statistic='count', bins=binsize)
    bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
    #set 0 to nan
    bin_statistic['statistic'] = np.where(bin_statistic['statistic'] == 0, np.nan, bin_statistic['statistic'])
    return bin_statistic

def outlier_filtering(array, binsize=(35, 35)):
    # Example data from array
    data = array.flatten()  # Flatten the data for easier processing

    # Calculate IQR using nan-safe functions
    Q1 = np.nanpercentile(data, 25)
    Q3 = np.nanpercentile(data, 75)
    IQR = Q3 - Q1

    # Define outliers
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Find maximum non-outlier value, ignoring nan
    valid_data = data[(data >= lower_bound) & (data <= upper_bound)]
    max_non_outlier = np.nanmax(valid_data) if np.any(np.isfinite(valid_data)) else np.nan

    # Substitute outliers, ignoring nan in comparisons
    data[(data > upper_bound) & ~np.isnan(data)] = max_non_outlier

    # Reshape data back to the original shape of array if needed
    processed_array = data.reshape(array.shape)

    # Set corners to zero, assuming the structure has at least binsize dimensions
    for i in range(processed_array.shape[0]):
        processed_array[i, 0, 0] = 0
        processed_array[i, 0, binsize[0] - 1] = 0
        processed_array[i, binsize[0] - 1, 0] = 0
        processed_array[i, binsize[0] - 1, binsize[0] - 1] = 0

    return processed_array
