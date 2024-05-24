import pandas as pd
from scipy.ndimage import gaussian_filter
from mplsoccer import Pitch, VerticalPitch, FontManager, Sbopen
import numpy as np


def preprocess_df(df, binsize = (35,35)):
    pitch = Pitch(pitch_type='opta')
    bin_statistic = pitch.bin_statistic(df.x, df.y, statistic='count', bins=binsize)
    bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
    return bin_statistic

def outlier_filtering (array, binsize = (35,35)):

    # Example data from array
    data = array.flatten()  # Flatten the data for easier processing

    # Calculate IQR
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1

    # Define outliers
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Find maximum non-outlier value
    max_non_outlier = np.max(data[(data >= lower_bound) & (data <= upper_bound)])

    # Substitute outliers
    data[(data > upper_bound)] = max_non_outlier

    # Reshape data back to the original shape of array if needed
    processed_array = data.reshape(array.shape)

    for i in range(processed_array.shape[0]):
        # Top-left corner
        processed_array[i, 0, 0] = 0
        # Top-right corner
        processed_array[i, 0, binsize[0] - 1] = 0
        # Bottom-left corner
        processed_array[i, binsize[0] - 1, 0] = 0
        # Bottom-right corner
        processed_array[i, binsize[0] - 1, binsize[0] - 1] = 0

    return processed_array
