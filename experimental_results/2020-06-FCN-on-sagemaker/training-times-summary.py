import re
import argparse
import json
import sys
import statistics

def main():

    time_data = json.load(sys.stdin)
    
    #json.load(fp, *, cls=None, object_hook=None, parse_float=None, parse_int=None, parse_constant=None, object_pairs_hook=None, **kw)
    sum_of_epochs_time = 0.0
    sum_of_validations_time = 0.0
    n_epochs = len(time_data["epochs"])
    sum_of_steps_time = 0.0
    n_steps = 0
    steps_times = []
    
    for ek, ev in time_data["epochs"].items():
        v_time = ev["validation_time"]
        e_time = ev["epoch_time"]
        sum_of_epochs_time += e_time
        sum_of_validations_time += v_time
        for ik, iv in ev["steps"].items():
            steps_times.append(iv)
            sum_of_steps_time += iv
            n_steps += 1

    total_time = time_data["total_training"]
    init_time = time_data["init"]
    print("Total training time: {:.6f}".format(total_time))
    print("Largest real time delta: {:.6f}".format(time_data["largest_real_time_delta"]))
    print(" - {:.2f} % of the total training time.".format(100*time_data["largest_real_time_delta"]/total_time))
    print("Initialization time: {:.6f}".format(init_time))
    print(" - {:.2f} % of the total training time.".format(100*init_time/total_time))
    print("Epochs")
    print("  Number of epochs: {:.6f}".format(n_epochs))
    print("  Total time spent on epochs: {:.6f}".format(sum_of_epochs_time))
    print("    - {:.2f} % of the total training time.".format(100*sum_of_epochs_time/total_time))
    print("  Average epoch time: {:.6f}".format(sum_of_epochs_time/n_epochs))
    print("Validations")
    print("  Total time spent on validations: {:.6f}".format(sum_of_validations_time))
    print("    - {:.2f} % of the total training time.".format(100*sum_of_validations_time/total_time))
    print("  Average validation time: {:.6f}".format(sum_of_validations_time/n_epochs))
    print("Steps")
    print("  Number of steps: {:.6f}".format(n_steps))
    print("  Average number of steps per epoch: {:.6f}".format(float(n_steps)/float(n_epochs)))
    print("  Total time spent on steps: {:.6f}".format(sum_of_steps_time))
    print("    - {:.2f} % of the total training time.".format(100*sum_of_steps_time/total_time))
    avg_step_time = sum_of_steps_time/n_steps
    print("  First step time: {:.6f}".format(steps_times[0]))
    print("  Average step time: {:.6f}".format(avg_step_time))
    TMiIavg=(sum_of_steps_time-steps_times[0])/(n_steps-1)
    print("  T Mi Iavg: {:.6f}".format(TMiIavg))
    print("  Outstanding step times: > 1.2x the average time")
    for ek, ev in time_data["epochs"].items():
        for ik, iv in ev["steps"].items():
            if iv > 1.2 * avg_step_time:
                print ("    - Epoch({}) Step({}) Time({:.3f}) - {:.2f} times larger than average".format(ek,ik,iv,iv/avg_step_time))
    print("Beta: {:.2f} %".format(100*(init_time+sum_of_validations_time+steps_times[0])/sum_of_steps_time))
    print("  - Initialization + Validations + 1st step time = {:.6f}".format(init_time+sum_of_validations_time+steps_times[0]))
    print("  - Remaining steps time = {:.6f}".format(sum_of_steps_time-steps_times[0]))
    print("T Mi Iavg prediction errors")
    if len(steps_times) >= 2:
        print("  - Step 2 of epoch 1: {:.6f} - Error: {:.2f} %".format(steps_times[1],abs(100*(steps_times[1]-TMiIavg)/TMiIavg)))
        if len(steps_times) >= 5:
            avg_steps_2_6 = statistics.mean(steps_times[1:5])
            print("  - Avg steps 2-6: {:.6f} - Error: {:.2f} %".format(avg_steps_2_6,abs(100*(avg_steps_2_6-TMiIavg)/TMiIavg)))
            if len(steps_times) >= 10:
                avg_steps_2_10 = statistics.mean(steps_times[1:9])
                print("  - Avg steps 2-10: {:.6f} - Error: {:.2f} %".format(avg_steps_2_10,abs(100*(avg_steps_2_10-TMiIavg)/TMiIavg)))
               
    #print(json.dumps(time_data,indent=4))

# Parse the a log file from stdin and returns a tuple with five values:
# 1- the initialization time (-1.0 in case it was not matched on the log file)
# 2- a dictionary mapping epoch number and step ids to step execution time.
# 3- a diction mapping epoch ids to validation time
# 4- a diction mapping epoch ids to epochs execution time
# 5- a list with all intervals (deltas) computed using the real wallclock time
def parse_input_log():

    rt_deltas = []
    validations = {}
    epochs = {}
    steps = {}
    step_pm=re.compile(r'\d+ step training time: \d+(\.\d+)?s')
    validation_pm=re.compile(r'Validation time: \d+(\.\d+)?')
    epoch_pm=re.compile(r'Epoch time: \d+(\.\d+)?s')
    init_pm=re.compile(r'\(\'Tempo de inicializacao: \', \d+(\.\d+)?\)')
    rt_pm=re.compile(r'Real time: \d+(\.\d+)?')
    dt_pm=re.compile(r'Duracao do treinamento: +\d+(\.\d+)?')
    first_rt = 0.0
    last_rt = 0.0
    epoch_id=1
    init_time = -1.0
    dt_time = -1.0

    for line in sys.stdin:
            # Parse steps times
            res=step_pm.search(line)
            if res != None:
                sline = line.split()
                step_i = int(sline[0])
                step_time = float(sline[4][:-1])
                #print("step,{},{},{}".format(epoch_id,step_i,step_time))
                if epoch_id not in epochs: epochs[epoch_id] = {}
                if "steps" not in epochs[epoch_id] : epochs[epoch_id]["steps"] = {}
                epochs[epoch_id]["steps"][step_i] = step_time
            # Parse validations times
            res=validation_pm.search(line)
            if res != None:
                sline = line.split()
                validation_time = float(sline[2][:-1])
                #print("validation,{},{}".format(epoch_id,validation_time))
                if epoch_id not in epochs: epochs[epoch_id] = {}
                epochs[epoch_id]["validation_time"] = validation_time
            # Parse epochs times
            res=epoch_pm.search(line)
            if res != None:
                sline = line.split()
                epoch_time = float(sline[2][:-1])
                #print("epoch,{},{}".format(epoch_id,epoch_time))
                if epoch_id not in epochs: epochs[epoch_id] = {}
                epochs[epoch_id]["epoch_time"] = epoch_time
                epoch_id = epoch_id + 1
            # Parse initialization time
            res=init_pm.search(line)
            if res != None:
                sline = line.split()
                init_time = float(sline[4][:-1])
                #print("init,{}".format(init_time))
            # Parse "duracao do treinamento
            res=dt_pm.search(line)
            if res != None:
                sline = line.split()
                dt_time = float(sline[3])
                #print("training duration,{}".format(dt_time))
            # Parse real times
            res=rt_pm.search(line)
            if res != None:
                sline = line.split()
                #Handle cases in which there is an 's' suffix on the time
                if sline[2][-1] == 's': real_time = float(sline[2][:-1])
                else: real_time = float(sline[2])
                if first_rt == 0.0: first_rt = real_time
                last_rt_delta = real_time-last_rt
                if last_rt > 0.0: rt_deltas.append(last_rt_delta)
                #if last_rt > 0.0: print("rt delta,{}".format(last_rt_delta))
                last_rt = real_time

    all_times = {"init": init_time,
                 "total_training": dt_time,
                 "epochs": epochs}
    return all_times
        
if __name__ == "__main__":
    main()
