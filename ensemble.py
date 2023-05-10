import json
import os
import sys
import statistics as s

def read_json(file_path):
    with open(file_path) as f:
        d = json.load(f)
        return d

def compute_ensemble_stats(incumbents_collected_stats):
    incumbent_stats = {incumbent: {} for incumbent in incumbents_collected_stats}
    for incumbent in incumbents_collected_stats:
        for stat in config["stats_and_column"]:
            data = sorted(incumbents_collected_stats[incumbent][stat])
            quantiles = s.quantiles(data, n=4)
            incumbent_stats[incumbent][stat] = {"min":data[0],"q1":quantiles[0],"median":quantiles[1],"q3":quantiles[2],"max":data[-1]}
    return incumbent_stats

def bundle_jsons():
    files = [f for f in os.listdir(config['stats_output_location']) if config['stat_base_file_name'] in f]
    mggg_runs = [read_json(config['stats_output_location'] + "/" + f) for f in files]
    incumbents = [incumbent["name"] for incumbent in config["incumbents"]]
    incumbents_collected_stats = {name:{stat:[] for stat in config["stats_and_column"]} for name in incumbents}
    for incumbent in incumbents:
        for data in mggg_runs:
            for stat in config['stats_and_column']:
                incumbents_collected_stats[incumbent][stat] += data[incumbent][stat]
    return incumbents_collected_stats

def save_incumbent_stats(incumbent_stats):
    file_name = config["ensemble_processing_location"] + "/" + config["ensemble_processing_file_name"] +'.json'
    with open(file_name, 'w') as file:
        json.dump(incumbent_stats, file, indent=4)

if len(sys.argv) != 2:
    print("improper usage of program. Use python ensemble.py config-file.json")
    sys.exit()

config = read_json(sys.argv[1])
incumbented_collected_stats = bundle_jsons()
incumbent_stats = compute_ensemble_stats(incumbented_collected_stats)
save_incumbent_stats(incumbent_stats)



