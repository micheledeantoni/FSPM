import numpy as np
from scipy.stats import t
from statsmodels.stats.multitest import multipletests

def perform_correlation_analysis(s_map, X, binsize, contrast, mtc = False):
    # Flatten maps for correlation analysis
    maps_flattened = s_map.reshape(s_map.shape[0], -1)  # Each row is a flattened heatmap for a match

    # Ensure X is a numpy array
    X = np.array(X)

    # Compute regression coefficients
    B = np.linalg.inv(X.T @ X) @ X.T @ maps_flattened

    # Compute residuals and variance
    residuals = maps_flattened - X @ B
    sigma_squared_hat = np.sum(residuals**2, axis=0) / (X.shape[0] - X.shape[1])
    cov_matrix = np.linalg.inv(X.T @ X)
    cov_B = np.array([sigma_squared * cov_matrix for sigma_squared in sigma_squared_hat])

    # Define contrast and calculate effect and its standard error
    contrast_effect = contrast @ B
    var_contrast_effect = (contrast @ cov_B) @ contrast.T
    se_contrast_effect = np.sqrt(var_contrast_effect)

    # T-statistic and p-values for a two-tailed test
    t_stats = contrast_effect / se_contrast_effect
    p_values = t.cdf(-np.abs(t_stats), df=X.shape[0] - X.shape[1]) * 2

    # Reshape back to map dimensions
    contrast_map = contrast_effect.reshape(binsize)
    p_value_map = p_values.reshape(binsize)

    # Optional: Correct for multiple comparisons
    flattened_p_vals = p_value_map.ravel()
    corrected_p_vals = multipletests(flattened_p_vals, method='fdr_bh')[1]
    corrected_p_map = corrected_p_vals.reshape(binsize)

    # Set the p-value threshold and create significant contrast map
    p_threshold = 0.05
    if mtc:
        significant_contrast_map = np.where(corrected_p_map < p_threshold, contrast_map, np.nan)
    else:
        significant_contrast_map = np.where(p_value_map < p_threshold, contrast_map, np.nan)

    # You can adjust this return statement to include more or fewer results as needed
    return contrast_map, significant_contrast_map

# Example usage:
# result = perform_correlation_analysis(s_map, X, binsize)
# contrast_map, p_value_map, corrected_p_map, significant_contrast_map = result

import numpy as np
from scipy.stats import t
from scipy.ndimage import label, generate_binary_structure
from statsmodels.stats.multitest import multipletests

def perform_correlation_analysis2(s_map, X, binsize, contrast, mtc=False, cluster_correction=False):
    # Flatten maps for correlation analysis
    maps_flattened = s_map.reshape(s_map.shape[0], -1)  # Each row is a flattened heatmap for a match

    # Ensure X is a numpy array
    X = np.array(X)

    # Compute regression coefficients
    B = np.linalg.inv(X.T @ X) @ X.T @ maps_flattened

    # Compute residuals and variance
    residuals = maps_flattened - X @ B
    sigma_squared_hat = np.sum(residuals**2, axis=0) / (X.shape[0] - X.shape[1])
    cond_number = np.linalg.cond(X.T @ X)
    #print("Condition number of the matrix:", cond_number)
    cov_matrix = np.linalg.inv(X.T @ X)
    cov_B = np.array([sigma_squared * cov_matrix for sigma_squared in sigma_squared_hat])

    # Calculate effect and its standard error
    contrast_effect = contrast @ B
    var_contrast_effect = (contrast @ cov_B) @ contrast.T
    se_contrast_effect = np.sqrt(var_contrast_effect)

    # T-statistic and p-values for a two-tailed test
    epsilon = 1e-8  # This value might need adjustment
    t_stats = contrast_effect / (se_contrast_effect + epsilon)
    p_values = t.cdf(-np.abs(t_stats), df=X.shape[0] - X.shape[1]) * 2

    # Reshape back to map dimensions
    contrast_map = contrast_effect.reshape(binsize)
    p_value_map = p_values.reshape(binsize)

    # Apply multiple comparison correction if specified
    if mtc:
        flattened_p_vals = p_value_map.ravel()
        corrected_p_vals = multipletests(flattened_p_vals, method='fdr_bh')[1]
        p_value_map = corrected_p_vals.reshape(binsize)

    # Apply cluster-based correction if specified
    if cluster_correction:
        # Define an adjacency structure that considers connections in 8 directions
        struct = generate_binary_structure(2, 2)
        # Apply an initial threshold to define potentially significant areas
        sig_mask = p_value_map < 0.05
        # Ensure t_stats is reshaped correctly to match the 2D structure of each layer
        t_stats = t_stats.reshape(binsize)

        # The rest remains the same
        labeled_array, num_features = label(sig_mask, structure=struct)
        cluster_sizes = np.array([np.sum(t_stats[labeled_array == i]) for i in range(1, num_features + 1)])
        size_threshold = np.percentile(cluster_sizes, 95)  # Assuming top 5% significance
        significant_clusters = np.isin(labeled_array, np.where(cluster_sizes > size_threshold)[0] + 1)
        significant_contrast_map = np.where(significant_clusters, contrast_map, np.nan)

    else:
        # Apply simple threshold-based significant map
        significant_contrast_map = np.where(p_value_map < 0.05, contrast_map, np.nan)

    return contrast_map, significant_contrast_map

# Example usage:
# contrast_map, significant_contrast_map = perform_correlation_analysis(s_map, X, (20, 20), np.array([0, 1, 0]), mtc=True, cluster_correction=True)
