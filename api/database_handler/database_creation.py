import csv
import pandas as pd

from api.database_handler.database_tables import db, Parameters
from ai import WeightCalculatorAI


def instantiate_database(parameters_location):
    """
    Instantiate the initial values of your database
    :param parameters_location: Location to the parameters csv file
    """
    # Read and parse the parameters from the file
    with open(parameters_location) as fp:
        parameters = list(csv.DictReader(fp))
        #weight_fixed:1.0, t1:2,..
        params_values = [{key: val for key, val in param.items() if key != 'parameter'} for param in parameters]
        #created_since, updated_since
        param_names = [param['parameter'] for param in parameters]
        parameters = {name: value for name, value in zip(param_names, params_values)}

    # Fill the database with initial(default) values
    for name, values in parameters.items():
        parameter = Parameters(name,
                               values['weight_fixed_default'],
                               values['weight_ai'],
                               values['thresh_T1_default'],
                               values['thresh_T2_default'],
                               values['description'],
                               values['reasoning'])
        db.session.add(parameter)
    db.session.commit()


def train_ai(parameters_location, dataset_location, verbose=False):
    """
    Train the AI
    :param parameters_location: Location to the parameters csv file
    :param dataset_location: Location of the dataset for training AI
    :param verbose: Set to True if you want AI to print training (it trains twice)
    """
    data = pd.read_csv(dataset_location)
    parameters = pd.read_csv(parameters_location)

    data = data.drop(columns=['package_name'])
    thresh_nominator = parameters.thresh_T1.to_numpy()
    thresh_denominator = parameters.thresh_T2.to_numpy()

    # Train and test the model
    model = WeightCalculatorAI(dim=data.shape[1] - 1, T=(thresh_nominator, thresh_denominator),
                               parameters_location='../parameters.csv')

    # Train model (and save the results)
    model.evaluate(data, verbose=verbose)
    model.fit(data, epochs=100, verbose=verbose)
    model.save_model()
    model.evaluate(data, verbose=verbose)


def create_database(db_reconstruct, parameters_file_location, ai_dataset_location):
    """
    Creation of database and its initialization at the start of running the server
    :param db_reconstruct: Boolean value saying if I should recreate the dataset
    :param parameters_file_location: Location to the parameters csv file
    :param ai_dataset_location: Location of the dataset for training AI
    """
    # Create SQL database
    if db_reconstruct:
        db.drop_all()  # Remove if you don't want to create a new database every time
        db.create_all()

    # Train the AI
    train_ai(parameters_file_location, ai_dataset_location)

    # Instantiate the database
    if db_reconstruct:
        instantiate_database(parameters_file_location)
