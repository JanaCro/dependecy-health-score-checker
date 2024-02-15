from flask import make_response, request, jsonify
from api.database_handler.database_tables import app, Parameters
from api.database_handler.database_creation import create_database
from calculators import CriticalityScoreCalculator


parameters_file_location = '../parameters.csv'
ai_dataset_location = '../ai/ai-data.csv'
db_reconstruct = True


@app.route('/score/<platform>/<package>/', methods=['GET'])
def calculate_crit_score(platform, package):
    try:
        # Get parameters for the calculator
        t1 = [p.t1 for p in Parameters.query.all()]
        t2 = [p.t2 for p in Parameters.query.all()]

        # Get the weights of markers
        ai_condition = 'ai' in request.args and request.args.get('ai').lower() in ["true", "t"]
        if ai_condition:
            weights = [p.weight_ai for p in Parameters.query.all()]
        else:
            weights = [p.weight_fixed for p in Parameters.query.all()]

        keys_ordered = [p.parameter_name for p in Parameters.query.all()]

        # Query parameters to change weight and thresholds
        for key, value in request.args.items():
            if key == 'ai':
                continue

            value = float(value)
            param_type, marker_name = key[:key.find('_')], key[key.find('_')+1:]
            if marker_name not in keys_ordered:
                raise ValueError(f"Marker {marker_name} does not exist!")
            if param_type not in ["w", "t1", "t2"]:
                raise ValueError(f"Parameter {param_type} is not a valid parameter!")

            idx = keys_ordered.index(marker_name)
            if param_type == 'w':
                weights[idx] = value
            elif param_type == 't1':
                t1[idx] = value
            elif param_type == 't2':
                t2[idx] = value

        # Calculate score
        cs_calculator = CriticalityScoreCalculator(keys_ordered, t1, t2)
        score, text = cs_calculator.calculate_criticality_score(package, platform, weights)

        return make_response(jsonify({'score': score, 'text': text, 'marker_values': cs_calculator.parameters}), 200)
    except Exception as e:
        return make_response(jsonify(e.args[0]), 500)


@app.route('/info/', methods=['GET'])
def get_user_info():
    # Get data from database
    parameter_defaults = Parameters.query.all()

    # Scrape data
    param_names = [p.parameter_name for p in parameter_defaults]
    descriptions = [p.description for p in parameter_defaults]
    reasons = [p.reasoning for p in parameter_defaults]
    ai_vals = [p.weight_ai for p in parameter_defaults]
    w_def_vals = [p.weight_fixed for p in parameter_defaults]
    t1_def_vals = [p.t1 for p in parameter_defaults]
    t2_def_vals = [p.t2 for p in parameter_defaults]


    # Get info
    info = {}
    for i, param_name in enumerate(param_names):
        info[param_name] = {
            'description': descriptions[i],
            'reasons': reasons[i],
            'ai_weights': ai_vals[i],
            'w_default': w_def_vals[i],
            't1_default': t1_def_vals[i],
            't2_default': t2_def_vals[i],
        }

    return make_response(jsonify(info), 200)



if __name__ == '__main__':
    with app.app_context():
        create_database(db_reconstruct, parameters_file_location, ai_dataset_location)
    app.run(debug=True)
