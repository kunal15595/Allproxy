import socket
import base64
import httplib
from threading import Thread
import re
import signal
import os
import sys

defaultIP = '8.8.8.8'

# import sys
# sys.stdout = open('./log/DNS.log', 'w+')


class DNSQuery:

	def __init__(self, data, addr):
		self.data = data
		self.addr = addr
		self.dominio = ''
		self.ip = defaultIP

		tipo = (ord(data[2]) >> 3) & 15   # Opcode bits
		if tipo == 0:                     # Standard query
			ini = 12
			lon = ord(data[ini])
			while lon != 0:
				self.dominio += data[ini + 1:ini + lon + 1] + '.'
				ini += lon + 1
				lon = ord(data[ini])
		if len(self.dominio) > 1:
			self.dominio = self.dominio[0:-1]


def respuesta(query):
	stat = 2
	
	if dnsCache.__contains__(query.dominio):
		query.ip = dnsCache[query.dominio]
	else:
		query.dominio = query.dominio.replace('_', '')
		if query.dominio.lower()[-12:] == '.appspot.com':
			query.ip = '74.125.224.208'
			stat = 0
		else:
			try:
				dnsConn = httplib.HTTPConnection(
					'gaednsproxy1.appspot.com', timeout=20)
				dnsConn.request(
					"GET", "/?d=" + base64.b64encode(base64.b64encode(query.dominio)))
				dnsRes = dnsConn.getresponse()
				query.ip = dnsRes.read()
				if dnsRes.status == 200:
					stat = 1
			except:
				print '{:5s}  {:25s} {:15s}'.format('Exc', str(query.ip), str(query.dominio))

			# add to dns cache
			if re.match('[0-9]+\.[0-9]+\.[0-9]+\.[0-9]', query.ip) and not query.ip == defaultIP:
				dnsCache[query.dominio] = query.ip
			else:
				print '{:5s}  {:15s} {:15s}'.format('Err', str(query.dominio), query.ip)
				return

	packet = ''
	if query.dominio:
		packet += query.data[:2] + "\x81\x80"
		# Questions and Answers Counts
		packet += query.data[4:6] + query.data[4:6] + '\x00\x00\x00\x00'
		# Original Domain Name Question
		packet += query.data[12:]
		# Pointer to domain name
		packet += '\xc0\x0c'
		# Response type, ttl and resource data length -> 4 bytes
		packet += '\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'
		# 4bytes of IP
		packet += str.join('', map(lambda x: chr(int(x)), query.ip.split('.')))

	udps.sendto(packet, query.addr)
	
	if stat == 1:
		print '{:5s}  {:15s} {:15s}'.format(str(dnsRes.status), str(query.ip), str(query.dominio))
	elif stat == 2 and not query.dominio == 'gaednsproxy1.appspot.com':
		print '{:5s}  {:20s} {:15s}'.format('Hit', str(query.ip), str(query.dominio))


def signal_term_handler(signal, frame):
	print 'SIGTERM'
	print 'Saving cache'
	a = file('./tproxy/dnsCache', 'w')
	for i in dnsCache:
		a.write(dnsCache[i].ljust(20) + '\t\t' + i + '\n')
	a.close()
	udps.close()
	sys.exit(0)

def writePidFile():
	pid = str(os.getpid())
	f = open(sys.argv[1], 'w')
	f.write(pid)
	f.close()

if __name__ == '__main__':

	signal.signal(signal.SIGTERM, signal_term_handler)
	signal.signal(signal.SIGINT, signal_term_handler)

	writePidFile()
	print 'DNS server running on port 55.'

	udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	udps.bind(('', 55))

	dnsCache = dict()
	try:
		a = file('./tproxy/defaultIPs', 'r')
		for i in a:
			line_ip = re.split("[, \-!?:\t\n]+", i)
			dnsCache[line_ip[1]] = line_ip[0]
		a.close()
		print 'Default IPs loaded'
	except:
		print 'Could not load default IPs'

	try:
		a = file('./tproxy/dnsCache', 'r')
		for i in a:
			line_ip = re.split("[\n \t]+", i)
			if re.match('[0-9]+\.[0-9]+\.[0-9]+\.[0-9]', line_ip[0]):
				dnsCache[line_ip[1]] = line_ip[0]
		a.close()
		print 'Cached IPs loaded'
	except:
		print 'Could not load cached IPs'

	try:
		while 1:
			data, addr = udps.recvfrom(1024)
			p = DNSQuery(data, addr)
			t = Thread(target=respuesta, args=(p,))
			t.start()
	except (KeyboardInterrupt, SystemExit):
		print 'Finalizing'
		a = file('./tproxy/dnsCache', 'w')
		for i in dnsCache:
			a.write(dnsCache[i].ljust(20) + '\t\t' + i + '\n')
		a.close()
		udps.close()
		sys.exit(0)
