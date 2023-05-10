import geopandas as gpd
gpd.options.use_pygeos = False
from gerrychain import (GeographicPartition, Partition, Graph, MarkovChain,
                        proposals, updaters, constraints, accept, Election)
from gerrychain.updaters import Tally, cut_edges
from gerrychain.proposals import recom
from functools import partial
import networkx as nx
import sys
import statistics as s
import json
import random
import string
import time


## collect config object location from command line argument ###
random.seed(time.time())

def read_config(file_path):
    with open(file_path) as f:
        d = json.load(f)
        return d


if len(sys.argv) != 2:
    print("improper usage of program. Use python seawulf.py config-file.json")
    sys.exit()

config = read_config(sys.argv[1])

######## Set Up MGGGG #####
graph = Graph.from_json(config["input_json"])
election = Election("election", {"Dem": "USH18D", "Rep": "USH18R"})
initial_partition = Partition(
    graph,
    assignment="district_2022",
    updaters = {
    "population":Tally("TOTPOP",alias="population"),
    "election":election
    }
)

pop_target = sum(initial_partition["population"].values()) / len(initial_partition)
proposal = partial(recom,pop_col="TOTPOP",pop_target=pop_target,epsilon=0.5,node_repeats=10)
pop_constraint = constraints.within_percent_of_ideal_population(initial_partition, 0.10)

chain = MarkovChain(
    proposal=proposal,
    constraints=[
        pop_constraint,
    ],
    accept=accept.always_accept,
    initial_state=initial_partition,
    total_steps=1000
)

#########################


#### Set Up variables for stats collection #######
district_to_incumbent_2020 = {}
incumbents_home_precincts = {}
incumbents_2020_precincts = {}
incumbents_collected_stats = {}


election_stats = {"safe seats":[]}

stats_and_column = config["stats_and_column"]

for entry in config['incumbents']:
    district_num,name,home = entry.values()
    incumbents_home_precincts[name] = home
    incumbents_collected_stats[name] = {x:[] for x in stats_and_column}
    incumbents_2020_precincts[name] = set({})
    district_to_incumbent_2020[district_num] = name

#############



### Create the initial set of precincts for each incumbent ###
for i in range(len(graph)):
    if graph.nodes[i]["districtr"] in district_to_incumbent_2020:
        incumbents_2020_precincts[district_to_incumbent_2020[graph.nodes[i]["districtr"]]].add(i)

def compute_stats(partition):
    incumbents_current_precincts = {x:set({}) for x in incumbents_2020_precincts}
    district_to_incumbent_current = {partition.assignment[incumbents_home_precincts[x]]:x for x in incumbents_home_precincts}
    
    # check that two incumbents aren't in the same district
    if (len(district_to_incumbent_current) != len(district_to_incumbent_2020)):
        print("unsuitable plan")
        return
    print("suitable plan")

    for i in range(len(partition.graph.nodes)):
        if (partition.assignment[i] in district_to_incumbent_current):
            incumbents_current_precincts[district_to_incumbent_current[partition.assignment[i]]].add(i)

    for incumbent in incumbents_collected_stats:
        for stat,col in stats_and_column.items():
            prec_only_2020 = incumbents_2020_precincts[incumbent] - incumbents_current_precincts[incumbent]
            prec_only_curr = incumbents_current_precincts[incumbent] - incumbents_2020_precincts[incumbent]
            prec_intersect = incumbents_2020_precincts[incumbent] &  incumbents_current_precincts[incumbent]
            combine_set_stat = lambda x: sum(list(map(lambda y: partition.graph.nodes[y][col] ,x)))
            var = combine_set_stat(prec_only_curr) / combine_set_stat(prec_only_2020 | prec_intersect)
            incumbents_collected_stats[incumbent][stat].append(var)


def save_plan(partition,votes,safe_seats):
    data = {"votes":votes,"safe_seats":safe_seats,"partition":[partition.assignment[n] for n in partition.assignment]}
    file_name = config["plans_output_location"] + "/" + config["plan_base_file_name"] + "_" + ''.join(random.choices(string.ascii_uppercase, k=10)) +'.json'
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)

def compute_election_results(partition):
    votes = []
    for dem_votes,rep_votes in zip(partition["election"].percents("Dem"),partition["election"].percents("Rep")):
       votes.append([dem_votes,rep_votes])
    # set safe seat threshold in config
    safe_seats = sum([1 if d > 0.55 or d < 0.45 else 0 for d,r in votes])
    save_plan(partition,votes,safe_seats)

incumbent_stats = {}
def compute_ensemble_stats():
    for incumbent in incumbents_collected_stats:
        incumbent_stats[incumbent] = {}
        for stat in stats_and_column:
            data = sorted(incumbents_collected_stats[incumbent][stat])
            quantiles = s.quantiles(data, n=4)
            incumbent_stats[incumbent][stat] = {"min":data[0],"q1":quantiles[0],"median":quantiles[1],"q3":quantiles[2],"max":data[-1]}


def save_collected_stats():
    file_name = config["stats_output_location"] + "/" + config["stat_base_file_name"] + "_" + ''.join(random.choices(string.ascii_uppercase, k=10)) +'.json'
    print("writing to",file_name)
    with open(file_name, 'w') as file:
        json.dump(incumbents_collected_stats, file, indent=4)

for p in chain:
    compute_stats(p)
    #compute_election_results(p)
save_collected_stats()



