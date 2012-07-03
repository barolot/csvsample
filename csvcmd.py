#!/usr/bin/env python
# coding: utf-8

import os
import sys
import csv
import argparse

__version__ = '0.1'

C_KEY_ATTR = 'attr'
C_KEY_NAME = 'name'
C_KEY_TYPE = 'type'
C_KEY_FLAG0 = 'flag0'
C_KEY_FLAG1 = 'flag1'
C_KEY_MODE_VAL = 'mode_val'
C_KEY_MODE_COMMENT = 'mode_comment'
C_KEY_MODE_MIN = 'mode_min'
C_KEY_MODE_MAX = 'mode_max'
C_KEY_PHYS_MIN = 'phys_min'
C_KEY_PHYS_MAX = 'phys_max'
C_KEY_PHYS_UNIT = 'phys_unit'
C_KEY_INIT_VALUE = 'init_value'
C_KEY_IDENTIFIER = 'identifier'
C_KEY_IDENT_LEN = 'ident_len'
C_KEY_IDENT_TYPE = 'ident_type'
C_KEY_TASK = 'task'
C_KEY_NAMESPACE = 'namespace'
C_KEY_UNIT_C = 'unit_c'
C_KEY_UNIT = 'unit'
C_KEY_RESOLUTION_S = 'resolution_s'
C_KEY_RESOLUTION_F = 'resoltuion_f'
C_KEY_MIN2 = 'min2'
C_KEY_MAX2 = 'max2'
C_KEY_INIT_VALUE2 = 'init_value2'

C_TYPE_VALUE_PHISICAL = '物理値'
C_TYPE_VALUE_FLAG = 'フラグ'
C_TYPE_VALUE_MODE = 'モード'
C_ACCESS_FIELD_MAX_COUNT = 159

## Parse options

def set_options(p, keyword):
	if keyword == 'infile':
		p.add_argument('incsvfile', action='store', help='csv file pre-converted from the original data file')
	if keyword == 'outfile':
		p.add_argument('outcsvfile', action='store', help='csv file to output results')

def parse_options():
	# create top-level parser
	parser = argparse.ArgumentParser(description="usage")
	parser.add_argument('-v', '--version', action='version', version=__version__, help='show program version and exit')
	
	# read config file if exist
	'''
	if os.environ.get('HOME'):
		CONFIGFILE = os.environ.get('HOME') + '/.csvcmd'
		if os.path.isfile(CONFIGFILE):
			'''

	# create subparsers
	subparsers = parser.add_subparsers(help='commands')
	# subcommand 'count'
	parser_count = subparsers.add_parser('count', help='count data records of each type')
	parser_count.add_argument('-p', action='store_true', help='print data name without type field')
	set_options(parser_count, 'infile')
	# subcommand 'list'
	parser_list = subparsers.add_parser('list', help='list data with various options')
	parser_list.add_argument('-m', action='store_true', help='list all module names')
	parser_list.add_argument('-d', action='store_true', help='list all data names')
	parser_list.add_argument('-a', action='store_true', help='list all module and data names')
	parser_list.add_argument('-l', action='store_true', help='list all data with values')
	parser_list.add_argument('-ma', action='store_true', help='list all module names in access fields')
	set_options(parser_list, 'infile')
	parser_list.set_defaults(func=list_data)
	# subcommand 'verify'
	parser_verify = subparsers.add_parser('verify', help='verify data records')
	set_options(parser_verify, 'infile')
	parser_verify.set_defaults(func=verify_data)
	# subcommand generate
	parser_generate = subparsers.add_parser('generate', help='generate access map')
	set_options(parser_generate, 'infile')
	set_options(parser_generate, 'outfile')
	parser_generate.set_defaults(func=generate_access_map)

#	args = vars(parser.parse_args())
	args = parser.parse_args()

	return args

## Internal functions

class UnicodeDictReader(csv.DictReader):
	def __init__(self, f, fieldnames=None, restkey=None, restval=None, dialect="excel", encoding="cp932", *args, **kwds):
		csv.DictReader.__init__(self, f, fieldnames, restkey, restval, dialect, *args, **kwds)
		self.encoding = encoding
	
	def decode(self, value):
		return value and value.decode(self.encoding) or value
		
	def next(self):
		d = csv.DictReader.next(self)
		for key in d:
			d[key] = self.decode(d[key])
		return d

def is_skip(r):
	return (r[C_KEY_ATTR] == 'X' or (r[C_KEY_NAME] == '' and r[C_KEY_TYPE] == ''))

def is_module(r):
	return (r[C_KEY_ATTR] == 'M')

def is_access_tab(r):
	return (r[C_KEY_ATTR] == 'A')

def is_valid_type(r):
	t = r[C_KEY_TYPE]
	return (t == C_TYPE_VALUE_PHISICAL or t == C_TYPE_VALUE_FLAG or t == C_TYPE_VALUE_MODE)

def is_valid_data2(r, l):
	for k in l:
		if r[k] == "":
			return False, (k + ' missing' )
	return True, ""
	
def is_valid_data(r):
	t = r[C_KEY_TYPE]
	if t == C_TYPE_VALUE_PHISICAL:
		l = [C_KEY_NAME, C_KEY_PHYS_MIN, C_KEY_PHYS_MAX, C_KEY_PHYS_UNIT, C_KEY_INIT_VALUE, C_KEY_IDENTIFIER, C_KEY_IDENT_LEN, C_KEY_IDENT_TYPE, C_KEY_RESOLUTION_S, C_KEY_MIN2, C_KEY_MAX2, C_KEY_INIT_VALUE2]
	elif t == C_TYPE_VALUE_FLAG:
		l = [C_KEY_NAME, C_KEY_FLAG0, C_KEY_FLAG1, C_KEY_INIT_VALUE, C_KEY_IDENTIFIER, C_KEY_IDENT_LEN, C_KEY_IDENT_TYPE, C_KEY_MAX2, C_KEY_INIT_VALUE2]
	elif t == C_TYPE_VALUE_MODE:
		l = [C_KEY_NAME, C_KEY_MODE_VAL, C_KEY_MODE_MIN, C_KEY_MODE_MAX, C_KEY_INIT_VALUE, C_KEY_IDENTIFIER, C_KEY_IDENT_LEN, C_KEY_IDENT_TYPE, C_KEY_MAX2, C_KEY_INIT_VALUE2]
	else:
		return False, "unknown type"
	
	return is_valid_data2(r, l)
	

def make_format(fs_l, delim=' '):
	fs = ""
	for x in fs_l:
		fs += x
		fs += delim
	fs = fs[0:len(fs)-1]
	return fs

## Subcommands

def count_data(args):
	infile = args.incsvfile
	with open(infile, 'rU') as f:
		reader = UnicodeDictReader(f)
		nline, nphysical, nflag, nmode, nmodule, nunknown, ntotal = 0, 0, 0, 0, 0, 0, 0
		for record in reader:
			nline += 1 # line number
			
			if is_skip(record):
				continue
			elif is_module(record):
				nmodule += 1
				continue
				
			t = record[C_KEY_TYPE]
			if t == C_TYPE_VALUE_PHISICAL:
				nphysical += 1
			elif t == C_TYPE_VALUE_FLAG:
				nflag += 1
			elif t == C_TYPE_VALUE_MODE:
				nmode += 1
			else:
				nunknown += 1
				if args.p == True:
					print("%04d missing type:%s" % (nline, record[C_KEY_NAME]))
			ntotal += 1

	print(u"物理値:%d フラグ:%d モード:%d Unknown:%d 合計:%d" % (nphysical, nflag, nmode, nunknown, ntotal))
	print(u"モジュール数:%d" % nmodule)

def list_data(args):
	infile = args.incsvfile
	with open(infile, 'rU') as f:
		reader = UnicodeDictReader(f)
		
		nline = 0
		for record in reader:
			nline += 1 # line number

			# List module names in access field, and break the loop
			if is_access_tab(record) and args.ma == True:
				for i in range(1, C_ACCESS_FIELD_MAX_COUNT+1):
					k = 'a%03d' % i
					l = record[k].split(os.linesep)
					print(l[len(l) - 1])
				break

			if is_skip(record):
				continue

			if args.m == True:
				if is_module(record):
					print(record[C_KEY_NAME])
			elif args.d == True:
				if is_valid_type(record):
					print(record[C_KEY_NAME])
			elif args.a == True:
				if is_module(record):
					print("m:%s" % record[C_KEY_NAME])
				elif is_valid_type(record):
					print("d:%s" % record[C_KEY_NAME])
			elif args.l == True:
				t = record[C_KEY_TYPE]
				if t == C_TYPE_VALUE_PHISICAL:
					fs = make_format(['%04d', '%s', '%s'])
					print(fs % (nline, record[C_KEY_NAME], t))
				elif t == C_TYPE_VALUE_FLAG:
					fs = make_format(['%04d', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'])
					print(fs % (nline, record[C_KEY_NAME], t, record[C_KEY_FLAG0], record[C_KEY_FLAG1], record[C_KEY_INIT_VALUE], record[C_KEY_IDENTIFIER], record[C_KEY_IDENT_LEN], record[C_KEY_IDENT_TYPE], record[C_KEY_MIN2], record[C_KEY_MAX2], record[C_KEY_INIT_VALUE2]))
				elif t == C_TYPE_VALUE_MODE:
					fs = make_format(['%04d', '%s', '%s'])
					print(fs % (nline, record[C_KEY_NAME], t))

def verify_data(args):
	infile = args.incsvfile
	with open(infile, 'rU') as f:
		reader = UnicodeDictReader(f)
		nline = 0
		for record in reader:
			nline += 1 # line number
			
			if is_skip(record) or is_module(record) or is_access_tab(record):
				continue
			
			ret, errmsg = is_valid_data(record)
			if(ret == False):
				print ("%d Error: %s %s" % (nline, errmsg, record[C_KEY_NAME]))

def generate_access_map(args):
	print("generate_access_map")
	return

def main():
	'''
	try:
		args = parse_options()
		args.func(args)
	except RuntimeError as e:
		sys.stderr.write("ERROR: %s¥n" % e)
		return
	except UnboundLocalError as e:
		sys.stderr.write("ERROR: %s¥n" % e)
		return
		'''
	args = parse_options()
	args.func(args)

if __name__ == '__main__':
	main()
