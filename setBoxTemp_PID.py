import sys
import time
from Lab5015_utils import SMChiller
from Lab5015_utils import read_box_temp
from optparse import OptionParser
from datetime import datetime
from simple_pid import PID

parser = OptionParser()

parser.add_option("--target", type=float, dest="target", default=22.0)
(options, args) = parser.parse_args()

debug = True

min_temp = options.target - 6.
max_temp = options.target + 1.

min_temp_safe = 10.
max_temp_safe = 30.

if options.target < min_temp or options.target > max_temp:
    print("### ERROR: set temperature outside allowed range ["+str(min_temp)+"-"+str(max_temp)+"]. Exiting...")
    sys.exit(-1)



SMC = SMChiller()

state = SMC.check_state()
print(">>> SMChiller::state: "+str(state))

if state is 0:
    print("--- powering on the chiller")
    SMC.set_state(1)
    time.sleep(5)
    state = SMC.check_state()
    print(">>> SMChiller::state: "+str(state))
    if state == 0:
        print("### ERROR: chiller did not power on. Exiting...")
        sys.exit(-2)


box_temp = 22.
while True:
    try:
        box_temp = float(read_box_temp())
        break
    except Exception as e:
        print(e)
        time.sleep(5)
        continue


water_temp = SMC.read_meas_temp()
new_temp = options.target - 1.
print("--- setting chiller water temperature at "+str(new_temp)+"° C   [box temperature: "+str(box_temp)+"° C   water temperature: "+str(water_temp)+"° C]")
SMC.write_set_temp(new_temp)
sleep_time = 900
print("--- sleeping for "+str(sleep_time)+" s\n")
time.sleep(sleep_time)
sys.stdout.flush()

pid = PID(0.3, 0., 50, setpoint=options.target)
pid.output_limits = (min_temp-options.target, max_temp-options.target)



while True:
    try:
        print(datetime.now())

        try:
            box_temp = float(read_box_temp())
        except Exception as e:
            print(e)
            time.sleep(5)
            continue
        
        output = pid(box_temp)
        new_temp += output
        
        #safety check
        new_temp = min([max([new_temp,min_temp]),max_temp])

        if debug:
            p, i, d = pid.components
            print("== DEBUG == P=", p, "I=", i, "D=", d)

        water_temp = SMC.read_meas_temp()
        print("--- setting chiller water temperature at "+str(round(new_temp, 1))+"° C   [box temperature: "+str(box_temp)+"° C   water temperature: "+str(water_temp)+"° C]")
        SMC.write_set_temp(round(new_temp, 1))
        sleep_time = 120
        print("--- sleeping for "+str(sleep_time)+" s   [kill at any time with ctrl-C]\n")
        time.sleep(sleep_time)
        sys.stdout.flush()
    
    except KeyboardInterrupt:
        break

print("--- powering off the chiller")
#SMC.set_state(0)
time.sleep(5)
state = SMC.check_state()
print(">>> SMChiller::state: "+str(state))
if state == 1:
    print("### ERROR: chiller did not power off. Exiting...")
    sys.exit(-3)
print("bye")
sys.exit(0)
