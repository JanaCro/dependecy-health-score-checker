from ai import WeightCalculatorAI
import pandas as pd
import numpy as np


if __name__ == '__main__':
    # Get the data (and set thresholds)
    data = pd.read_csv('ai-data.csv')
    parameters = pd.read_csv('../parameters.csv')
    if len(set(data['package_name'])) != data.shape[0]:
        duplicate_indexes = data[data.duplicated(subset=['package_name'], keep=False)].index
        raise ValueError(f"The same package is mentioned multiple times on rows: {duplicate_indexes.values+1}")
    data = data.drop(columns=['package_name'])
    thresh_nominator = parameters.thresh_T1.to_numpy()
    thresh_denominator = parameters.thresh_T2.to_numpy()

    # Train and test the model
    model = WeightCalculatorAI(dim=data.shape[1]-1, T=(thresh_nominator, thresh_denominator), parameters_location='../parameters.csv', path='model_weights')

    # Train model
    model.evaluate(data)
    model.fit(data, epochs=1_000)
    model.save_model()
    model.evaluate(data)

    # Save the weights of the model
    print("Formula weights", model.get_weights())
