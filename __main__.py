import argparse
import importlib.util
import inspect
import json
import sys
from import_data import *

parser = argparse.ArgumentParser(prog='Model of sorting center', allow_abbrev=True)

parser.add_argument('-map', '-m', type=argparse.FileType(), required=True,
                    metavar="FILE",
                    help='path to map configuration')
parser.add_argument('-type', '-t', type=argparse.FileType(), required=True,
                    metavar="FILE",
                    help='path to robots\' type configuration')
parser.add_argument('-position', '-p', type=argparse.FileType(), required=True,
                    metavar="FILE",
                    help='path to map configuration')
parser.add_argument('-distribution', '-d', type=argparse.FileType(), required=True,
                    metavar="FILE",
                    help='path to probability distribution configuration')
parser.add_argument('-algorithm', '-a', type=str, required=True,
                    metavar="FILE",
                    help="path to algorithm, file must contains "
                         "exactly one class inherited form Brain")
# TODO
# parser.add_argument('-parameters', '-p', nargs='*',
#                     help="parameters to algorithm")
parser.add_argument('-mode', required=True,# metavar="MODE",
                    choices=("run", "record", "average"),
                    help="mode to run. "
                         "RUN: runs model for time, outputs number of delibered mails; "
                         "RECORD: record all robots' action in csv; "
                         "AVERAGE: runs model for time several times to determine\n"
                         "average and standard deviation;"
)
parser.add_argument('-time', required=True, type=int,
                    help='model time to execute')
parser.add_argument('-output', '-o', type=argparse.FileType('w'),
                    help='file to output', default=sys.stdout)
parser.add_argument('-count', '-c', type=int,
                    help='how many time will be executed to calculate average, for -mode=average')

args = parser.parse_args()

# import algorithm
spec = importlib.util.spec_from_file_location("algorithm", args.algorithm)
algorithm = importlib.util.module_from_spec(spec)
sys.modules["algorithm"] = algorithm
spec.loader.exec_module(algorithm)

# find brain
brains = []
for name, obj in inspect.getmembers(algorithm):
    if (inspect.isclass(obj)
            and 'Brain' in (i.__name__ for i in obj.__mro__)
            and name != "Brain"
            and name != "OnlineBrain"):
        brains.append(obj)
if len(brains) == 0:
    print("No algorithm was found: ", file=sys.stderr)
    raise SystemExit(1)
if len(brains) > 1:
    print(f"More than one algorithm were found: ", file=sys.stderr, end='')
    print(*(i.__name__ for i in brains), file=sys.stderr, sep=', ')
    raise SystemExit(1)

# import
model = Model()
factory = import_distributions(model, json.load(args.distribution), *import_map_stations(json.load(args.map)))
args.map.seek(0)
map_ = import_map(model, json.load(args.map), factory)[0]
model.set_map(map_)
robot_type = import_robot_type(json.load(args.type))
model.set_brain(brains[0](model))
model.add_robots(import_robots(model, json.load(args.position), robot_type))

# run
match args.mode:
    case "run":
        model.run(args.time)
        print(model.delivered_mails, file=args.output)
    case "record":
        model.record_actions_for_time(args.time, args.output)
    case "average":
        if args.count is None:
            parser.error("count must be presented in -mode=average")
        if args.count < 2:
            parser.error("count must be greater than 2")
        print(*model.test(args.time, args.count), file=args.output)
