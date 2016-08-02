import psutil
import threading
import time
import math
import signal,sys
times = 600
process_pid = 3732
cpu = []
memory = []

def save(path,data,mode):
    file = open(path,mode)
    file.write(data)
    file.close()
def sig_exit(signalNum, e):
	times = 0
	save('cpu.txt','-----------------%s'%time.ctime() + '\n','a')
	save('cpu.txt','cpu = ' + str(cpu) + '\n','a')
	save('cpu.txt','memory = ' + str(memory) + '\n','a')
	sys.exit(0)
	 
def main():
	global process_pid
	global times
	signal.signal(signal.SIGINT, sig_exit)
	signal.signal(signal.SIGTERM, sig_exit)
	while times > 0:
		c = psutil.Process(pid = process_pid).cpu_percent(interval = 1)
		cpu.append(round(c,1))
		m = psutil.Process(pid = process_pid).memory_percent()
		memory.append(round(m,1))
		time.sleep(1)
		times = times - 1

		
main()

