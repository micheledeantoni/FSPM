import numpy as np
from scipy.stats import t
from scipy.ndimage import label, generate_binary_structure
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



def perform_correlation_analysis2(s_map, X, binsize, contrast, mtc=False, cluster_correction=False):
    # Flatten maps for correlation analysis
    maps_flattened = s_map.reshape(s_map.shape[0], -1)

    # Identify columns that do not contain any nan values
    valid_columns = ~np.isnan(maps_flattened).any(axis=0)
    maps_flattened_clean = maps_flattened[:, valid_columns]

    X = np.array(X)

    # Handle potentially ill-conditioned matrix
    if np.linalg.cond(X.T @ X) > 1/np.finfo(float).eps:
        reg_value = 1e-5
        B = np.linalg.inv(X.T @ X + reg_value * np.eye(X.shape[1])) @ X.T @ maps_flattened_clean
    else:
        B = np.linalg.inv(X.T @ X) @ X.T @ maps_flattened_clean

    residuals = maps_flattened_clean - X @ B
    sigma_squared_hat = np.sum(residuals**2, axis=0) / (residuals.shape[0] - X.shape[1])
    cov_matrix = np.linalg.inv(X.T @ X)
    cov_B = np.array([sigma_squared * cov_matrix for sigma_squared in sigma_squared_hat])

    contrast_effect = contrast @ B
    var_contrast_effect = (contrast @ cov_B) @ contrast.T
    se_contrast_effect = np.sqrt(np.nan_to_num(var_contrast_effect))

    epsilon = 1e-8
    t_stats = contrast_effect / (se_contrast_effect + epsilon)
    p_values = 2 * t.cdf(-np.abs(t_stats), df=X.shape[0] - X.shape[1])

    # Create full-sized maps with NaNs where valid data is missing
    full_size_contrast_map = np.full(s_map.shape[1] * s_map.shape[2], np.nan)
    full_size_p_value_map = np.full(s_map.shape[1] * s_map.shape[2], np.nan)

    full_size_contrast_map[valid_columns] = contrast_effect
    full_size_p_value_map[valid_columns] = p_values

    # Reshape these full-sized maps to original dimensions
    contrast_map = full_size_contrast_map.reshape(binsize)
    p_value_map = full_size_p_value_map.reshape(binsize)

    if mtc:
        corrected_p_vals = multipletests(p_value_map.ravel(), method='fdr_bh')[1]
        p_value_map = corrected_p_vals.reshape(binsize)

    if cluster_correction:
        struct = generate_binary_structure(2, 2)
        sig_mask = p_value_map < 0.05
        t_stats_map = np.full(s_map.shape[1] * s_map.shape[2], np.nan)
        t_stats_map[valid_columns] = t_stats
        t_stats_map = t_stats_map.reshape(binsize)

        labeled_array, num_features = label(sig_mask, structure=struct)
        cluster_sizes = np.array([np.sum(t_stats_map[labeled_array == i]) for i in range(1, num_features + 1)])
        if cluster_sizes.size > 0:
            size_threshold = np.percentile(cluster_sizes, 95)
            significant_clusters = np.isin(labeled_array, np.where(cluster_sizes > size_threshold)[0] + 1)
            significant_contrast_map = np.where(significant_clusters, contrast_map, np.nan)
        else:
            significant_contrast_map = np.full(binsize, np.nan)
    else:
        significant_contrast_map = np.where(p_value_map < 0.05, contrast_map, np.nan)

    return contrast_map, significant_contrast_map


def perform_correlation_analysis_backup(s_map, X, binsize, contrast, mtc=False, cluster_correction=False):
    # Flatten maps for correlation analysis
    maps_flattened = s_map.reshape(s_map.shape[0], -1)  # Each row is a flattened heatmap for a match

    # Ensure X is a numpy array
    X = np.array(X)

    # Compute regression coefficients
    B = np.linalg.inv(X.T @ X) @ X.T @ maps_flattened

    # Compute residuals and variance safely
    residuals = maps_flattened - X @ B
    # Mask out nan values for safe operations
    non_nan_mask = ~np.isnan(residuals)
    # Only compute on non-nan entries
    sigma_squared_hat = np.sum(residuals[non_nan_mask]**2, axis=0) / (non_nan_mask.sum(axis=0) - X.shape[1])

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
