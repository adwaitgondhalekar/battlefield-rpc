# Project Title

Battlefield Simulation using Remote Procedure Calls

## Prerequisites

These instructions will install the necessary libraries required to run this project.

```
pip install colorama 
pip install grpcio
pip install grpcio-tools
```

### How to run the code

Before running the server.py file and client.py file there are some changes that are needed to be done in both the files :- 
check for variables “own_ip_addr” and “others_ip_addr” and make necessary changes as to which system will run the "server.py" file and which will run "client.py" file.

####First start the server using the command

```
python3 server.py N M t T S1 S2 ... SM
```

here N = size of grid i.e. N*N
here M = total number of soldiers in the game
here t  = the periodic time after which missile will be fired
here T = Total Game Time

here S1 S2 .... SM represents the speed of the respective soldiers in the game

All of these are python command line arguments required to pass to run the "server.py" file
The soldier positions are assigned randomly at the start of the game.

Next we need to run the "client.py" file on another system

####Instructions to run client.py file

```
python3 client.py
```

After this the "client.py" starts execution and the simulated soldiers except for the commander are spawned, wherein for every incoming missile the soldiers try to take shelter by repositioning themselves.

##Authors

* **Ritwik Basak**
* **Adwait Gondhalekar**



