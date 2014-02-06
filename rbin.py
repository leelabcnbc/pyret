'''
rbin

tools for interacting with binary recording files

(C) 2014 Benjamin Naecker
'''

# Imports
from os import path
import scipy as sp

def readbin(fname, chan=0):
	'''
	usage:	dat = readbin(fname, chan=0)
	read a binary recording file

	input:
		fname	- string filename to read as binary
		chan	- which channel to read. raises IndexError if not in the file

	output:
		data	- data from the channel requested
	'''
	
	# Type of binary data, 16-bit unsigned integers
	uint = sp.dtype('>i2')

	# Check file exists
	if not path.exists(fname):
		print('Requested bin file {f} does not exist'.format(f = fname))
		raise FileNotFoundError

	# Read the header
	hdr = readbinhdr(fname)

	# Context manager to read the file (automagically closes when done)
	with open(fname, 'rb') as fid:

		# Check that the requested channel is in the recording
		if chan not in hdr['channel']:
			print('Requested channel {c} is not in the file'.format(c = chan))
			raise IndexError

		# Compute number of blocks and channel offsets
		nblocks = int(hdr['nsamples'] / hdr['blksize']) * uint.itemsize
		skip = hdr['nchannels'] * hdr['blksize'] * uint.itemsize
		chanoffset = chan * hdr['blksize'] * uint.itemsize

		# Preallocate ndarray to return the values
		dat = sp.zeros((hdr['nsamples'],))

		# Read the requested channel, a block at a time
		fid.seek(hdr['hdrsize'])
		for block in range(nblocks):
			# Compute start of the block and set the file position
			pos = hdr['hdrsize'] + block * skip + chanoffset
			fid.seek(pos)

			# Read the data
			dat[block * hdr['blksize'] : (block + 1) * hdr['blksize']] = \
				sp.fromfile(fid, dtype = uint, count = hdr['blksize'])

	# Scale and offset
	dat *= hdr['gain']
	dat += hdr['offset']

	# Return the data
	return dat

def readbinhdr(fname):
	'''
	usage:	hdr = readbinhdr(fname)
	read the header from a binary recording file

	input:
		fname	- string filename to read as binary

	output:
		hdr		- dictionary with header contents
	'''
	
	# Define datatypes to be read in
	uint 	= sp.dtype('>u4') 	# Unsigned integer, 32-bit
	short 	= sp.dtype('>i2') 	# Signed 16-bit integer
	flt 	= sp.dtype('>f4') 	# Float, 32-bit
	uchar 	= sp.dtype('>B') 	# Unsigned char

	# Read the header
	with open(fname, 'rb') as fid:
		hdr = {}
		hdr['hdrsize'] 		= sp.fromfile(fid, dtype = uint, count = 1) 				# size of header (bytes)
		hdr['type']			= sp.fromfile(fid, dtype = short, count = 1)				# not sure
		hdr['version']		= sp.fromfile(fid, dtype = short, count = 1) 				# not sure
		hdr['nsamples']		= sp.fromfile(fid, dtype = uint, count = 1) 				# samples in file
		hdr['nchannels']	= sp.fromfile(fid, dtype = uint, count = 1) 				# number of channels
		hdr['channel'] 		= sp.fromfile(fid, dtype = short, count = hdr['nchannels'])# channels
		hdr['fs']			= sp.fromfile(fid, dtype = flt, count = 1)					# sample rate
		hdr['blksize'] 		= sp.fromfile(fid, dtype = uint, count = 1)				# sz of data blocks
		hdr['gain']			= sp.fromfile(fid, dtype = flt, count = 1)					# amplifier gain
		hdr['offset']		= sp.fromfile(fid, dtype = flt, count = 1)					# amplifier offset
		hdr['datesz']		= sp.fromfile(fid, dtype = uint, count = 1)				# size of date string
		tmpdate				= sp.fromfile(fid, dtype = uchar, count = hdr['datesz'])	# date
		hdr['timesz']		= sp.fromfile(fid, dtype = uint, count = 1)				# size of time string
		tmptime				= sp.fromfile(fid, dtype = uchar, count = hdr['timesz'])	# time
		hdr['roomsz']		= sp.fromfile(fid, dtype = uint, count = 1)				# size of room string
		tmproom				= sp.fromfile(fid, dtype = uchar, count = hdr['roomsz'])	# room

	# Convert the date, time and room to strings
	hdr['date'] = ''.join([chr(i) for i in tmpdate])
	hdr['time'] = ''.join([chr(i) for i in tmptime])
	hdr['room'] = ''.join([chr(i) for i in tmproom])

	# Return the header
	return hdr
