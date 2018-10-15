#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys

cmdline_args = (
	(("-v", "--verbose"), {
		"action":	"store_true",
		"help":		"Verbose output",
	}),
	(("-i", "--infile"), {
		"type":		argparse.FileType("r"),
		"default":	sys.stdin,
		"help":		"Which file to read DB from (default: stdin)",
	}),
	(("-l", "--logdir",), {
		"metavar":	"LOGDIR",
		"type":		str,
		"default":	os.getcwd(),
		"help":		"Where to grep from (default: CWD)",
	}),
	(("pattern",), {
		"metavar":	"PATTERN",
		"type":		str,
		"help":		"Regex pattern (as in Python's re module)",
	}),
	(("who",), {
		"metavar":	"WHO",
		"type":		str,
		"nargs":	"+",
		"help":		"Who said it (1 or more nicks)",
	}),
)

def parse_args(argv):
	parser = argparse.ArgumentParser(prog=argv[0])
	for arg_name, arg_params in cmdline_args:
		parser.add_argument(*arg_name, **arg_params)
	
	return parser.parse_args(argv[1:])

def dejsonize(log_json):
	return dict((k, set(v)) for k, v in log_json.items())

# Will raise KeyError when encountering a nick not in the logs. Otherwise
# returns the union of all the log file namess associated with all the nicks.
def get_logfns(dbf, nicks):
	log_db = dejsonize(json.load(dbf))
	return set().union(*(log_db[nick] for nick in nicks))

def do_grep_one_file(prg, fn):
	with open(fn, "rb") as f:
		for line in (rawline.strip() for rawline in f):
			match = prg.search(line)
			if (match is not None):
				yield line

def do_grep(pattern, fns):
	prg = re.compile(pattern.encode("utf-8"))
	for fn in fns:
		for result in do_grep_one_file(prg, fn):
			yield result

def main(argv):
	args = parse_args(argv)
	try:
		logfns = get_logfns(args.infile, args.who)
		for result in do_grep(args.pattern, logfns):
			print(result.decode("utf-8"))

		return 0
	except KeyError as e:
		print("No such nick %s in DB" % e, file=sys.stderr)
		return 1

if (__name__ == "__main__"):
	sys.exit(main(sys.argv))
