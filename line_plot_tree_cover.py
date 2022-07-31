from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--shape_file", type=str)
args = parser.parse_args()

print(args.shape_file.split('/')[-1])
