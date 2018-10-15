#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys

getnick = b"^[0-9:]{4,8} ?<[\+@]?([^ ]+)>"

cmdline_args = (
	(("-v", "--verbose"), {
		"action":	"store_true",
		"help":		"Verbose output",
	}),
	(("-o", "--outfile"), {
		"type":		argparse.FileType("w"),
		"default":	sys.stdout,
		"help":		"Which file to output to (default: stdout)",
	}),
	(("logdir",), {
		"metavar":	"LOGDIR",
		"type":		str,
		"help":		"Which dir to crawl",
	}),
)

def nicks_from_log(prg, fn):
	with open(fn, "rb") as f:
		return nicks_from_lines(prg, f)

def nicks_from_lines(prg, lines):
	nicks = set()
	for match in (prg.search(line) for line in lines):
		if (not match):
			continue
		nick = match.group(1)
		nicks.add(nick)

	return nicks

# The dicts are the form of {nick1: {log1, log2, log3}, nick2: {log2, log4, log5}}
# etc. Finds keys common for both a and b, combines their associated sets, and
# adds other key-value pairs unmodified.
def merge_nickdicts(a, b):
	result = {}
	a_keys = set(a)
	b_keys = set(b)
	commons = a_keys.intersection(b_keys)
	a_uniqs = a_keys.difference(commons)
	b_uniqs = b_keys.difference(commons)

	for k in commons:
		a_vals = a[k]
		b_vals = b[k]
		combined = a_vals.union(b_vals)
		result[k] = combined
	
	for k in a_uniqs:
		result[k] = a[k]

	for k in b_uniqs:
		result[k] = b[k]
	
	return result

def crawl_logdir(prg, logdir, verbose = False):
	result = {}
	for fn in os.listdir(logdir):
		fp = os.path.join(logdir, fn)
		if (os.path.isfile(fp)):
			if (verbose):
				print(fp)
			for nick in nicks_from_log(prg, fp):
				if (nick not in result):
					result[nick] = set()
				result[nick].add(fp)

		elif (os.path.isdir(fp)):
			dir_conts = crawl_logdir(prg, fp, verbose=verbose)
			result = merge_nickdicts(dir_conts, result)
	return result

# From log_dict with format
# {
#	b"key0": {"log0", "log1"},
#	b"key1": {"log1", "log3"}
# }, create a JSON-compatible result dict with format
# {
#	"key0": ["log0", "log1"],
#	"key1": ["log1", "log3"]
# }
def jsonize(log_dict):
	return dict((k.decode("utf-8"), list(v)) for k, v in log_dict.items())

def parse_args(argv):
	parser = argparse.ArgumentParser(prog=argv[0])
	for arg_name, arg_params in cmdline_args:
		parser.add_argument(*arg_name, **arg_params)
	
	return parser.parse_args(argv[1:])

def main(argv):
	args = parse_args(argv)
	if (args.outfile is sys.stdout or args.outfile is sys.stderr):
		dump_params = {"indent": 4, "sort_keys": True}
	else:
		dump_params = {}

	prg = re.compile(getnick) # TODO: allow user to adjust this?
	logs = crawl_logdir(prg, args.logdir, verbose=args.verbose)
	json.dump(jsonize(logs), args.outfile, **dump_params)

if (__name__ == "__main__"):
	sys.exit(main(sys.argv))
