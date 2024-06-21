import numpy as np
from statsmodels.regression.linear_model import OLS

def perform_regression_with_contrast(Y, X, contrast_index, positive=True):
    results = []
    for i in range(Y.shape[1]):
        model = OLS(Y[:, i], X)
        result = model.fit()
        results.append(result)
    try :
        pvals = np.array([result.pvalues.iloc[contrast_index] for result in results])
        coefs = np.array([result.params.iloc[contrast_index] for result in results])
    except:
        pvals = np.array([result.pvalues[contrast_index] for result in results])
        coefs = np.array([result.params[contrast_index] for result in results])


    if not positive:
        coefs = -coefs

    return coefs, pvals
