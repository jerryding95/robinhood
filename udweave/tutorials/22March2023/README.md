# IMPORTANT NOTE

There has been several changes in UDWeave since this tutorial was created. Please refer to a more up to date version of the documentation.

# Introduction to UDWeave

UDWeave is a prototype compiler that transforms Weave programs into UpDown programs. Currently, the UpDown program that results from executing this compiler is a python program.

It is important to understand that UDWeave do not write the top program, but rather produces code to be executed in UpDown. In particular right now, it will produce the python file that contains the EFA code to be executed in FastSim or Gem5.

## Prerequisits
For this tutorial, it is expected that you are familiar with:
* The UpDown architecture (See ISAv2 Reference Manual and Previous publications)
* The UpDown software infrastructure (see programming reference manual and other examples)
* Be clear about the difference between *Top program* and *UpDown program*

## Basic information
UDWeave is built in Python. It can be executed using the python command with the entry script or directly:

```Bash
./UDWeave.py [...]
python UDWeave.py [...]
```

By default, UDWeave will show the version and usage. 

```Bash
> ./UDweave.py 
UpDown Weave Compiler - Version 0.1
usage: UDweave.py [-h] [--input INPUT] [-dp] [-dl] [-d DEB_LEVEL] [--ast-dump] [--weave-ir] [--opts OPTS] [--output OUTPUT]
```

But it is possible to see the whole help menu with `-h`

```Bash
> ./UDweave.py -h
usage: UDweave.py [-h] [--input INPUT] [-dp] [-dl] [-d DEB_LEVEL] [--ast-dump] [--weave-ir] [--opts OPTS] [--output OUTPUT]

UpDown Weave compiler

optional arguments:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        input file
  -dp, --debug-parser   Enable debug parser
  -dl, --debug-lexer    Enable debug parser
  -d DEB_LEVEL, --debug-level DEB_LEVEL
                        Set debug level
  --ast-dump            Dump Abstract Syntax Tree and stop
  --weave-ir            Generate Weave IR and stop
  --opts OPTS           Define Optimization Passes
  --output OUTPUT, -o OUTPUT
                        Output file
```

For the sake of this tutorial we will focus in the `-i`/`--input` and `-o`/`--output` flags.

## Hello world

Let's create our first program that contains a simple thread and event. 

This program will use the `begin()` event to send a new event that executes `end()` to the same lane.

### Step 0 - Create the thread and events

Threads are always necessary. Events must leave inside of a thread. The minimum program for UDWeave must contain a single thread, although this program is useless by itself.

```C
thread helloWorld {
    event begin() { }

    event end() {  }
}
```
Let us build this program with the following command:

```bash
> ./UDweave.py -i tutorials/22March2023/HelloWorld/step0.udw -o step0.py
```

The output of this program is the following:

```python
from EFA import *

def EFA_step0():
  efa = EFA([])
  efa.code_level = 'machine'
  state0 = State() #Only one state code 
  efa.add_initId(state0.state_id)
  efa.add_state(state0)

  event_map = {
    "helloWorld::begin" : 0,
    "helloWorld::end" : 1
  }

  # Writing code for event helloWorld::begin
  tran0 = state0.writeTransition("eventCarry", state0, state0, event_map['helloWorld::begin'])
  tran0.writeAction(f"entry: yield") 
  
  # Writing code for event helloWorld::end
  tran1 = state0.writeTransition("eventCarry", state0, state0, event_map['helloWorld::end'])
  tran1.writeAction(f"entry: yield") 
  
  return efa

```

Notice that this program will create a python function containing the equivalent EFA program. If using the [FastSim](https://bitbucket.org/achien7242/updown/src/master/) in the runtime system, one may use this program by using the resulting `step0.py` python file.

```C++
  UpDown::SimUDRuntime_t *rt = new UpDown::SimUDRuntime_t(machine, "step0", "EFA_step0", "./");
```

Also notice that this generated program creates a dictionary called `event_map` that contains two events (as described by the UDweave program). The name of the events use the thread name as namespace. This is to avoid collision when multiple threads are created containing events with the same name. 

Two transitions are created, one per each event. And, since no `yield_terminate` is explicitly used, the implicit `yield` will be added at the end of each event.

### Step 1 - Create the event word

To do our next step we will modify the current event word (i.e.,`CEVNT`) to build a new event word stored in `evWord`.
For creating the new event word based on the current event we will use the intrinsic function `evw_update_event(long unsigned evWord, EventLabel, int unsigned numOps)`.
This will result in an event word that is the same as the current event word, except for the `eventID`. The `eventID` field of the event word will be 
replaced by the ID of the `end()` event.

```C
thread helloWorld {
    event begin() {
        long evWord;
        // evw_update_event(Source Event Word, Event Label, Number of Operands)
        evWord = evw_update_event(CEVNT, end, 0);
    }

    event end() {  }
}
```

Let us build this program with UDweave using the following command

```bash
> ./UDweave.py -i tutorials/22March2023/HelloWorld/step1.udw -o step1.py
```

The resulting python file is

```python
from EFA import *

def EFA_step1():
  efa = EFA([])
  efa.code_level = 'machine'
  state0 = State() #Only one state code 
  efa.add_initId(state0.state_id)
  efa.add_state(state0)

  event_map = {
    "helloWorld::begin" : 0,
    "helloWorld::end" : 1
  }

  # Writing code for event helloWorld::begin
  tran0 = state0.writeTransition("eventCarry", state0, state0, event_map['helloWorld::begin'])
  ## evw_update_event(Source Event Word, Event Label, Number of Operands)
  tran0.writeAction(f"entry: ew_update_1 X2 X16 {event_map['helloWorld::end']} 1") 
  tran0.writeAction(f"ew_update_1 X16 X16 0 2") 
  tran0.writeAction(f"yield") 
  
  # Writing code for event helloWorld::end
  tran1 = state0.writeTransition("eventCarry", state0, state0, event_map['helloWorld::end'])
  tran1.writeAction(f"entry: yield") 
  
  return efa
```

The general structure of the program is the same as in Step 0 above. There are two additions.

First, the comment in line 4 has been bypassed to python generating an inline comment in the same location. 

Second, more importantly, the `evw_update_event()` intrinsic has been translated to 2 `ew_update_1` instructions. The first one changes the eventword, the second one changes the number of operands.

### Step 2 - Creating a thread local variable
Let us create a thread local variable. This variable will live for the duration of the thread, hence it will be kept from one event instantiation to the next one. 

```C
thread helloWorld {
    int aThreadLocal;

    event begin() {
        aThreadLocal = 0;
        long evWord;
        // evw_update_event(Source Event Word, Event Label, Number of Operands)
        evWord = evw_update_event(CEVNT, end, 0);
        aThreadLocal = aThreadLocal + 1;
    }

    event end() {
        aThreadLocal = aThreadLocal - 1;
    }
}
```

Notice that thread local variables are defined inside of a thread but outside of events. Also, these variables cannot be initialized with the definition. Hence, we initialize this variable at the `begin()` event.

Let's build this example so we can discuss it

```bash
> ./UDweave.py -i tutorials/22March2023/HelloWorld/step2.udw -o step2.py
```

The result if this compilation is as follows.

```python
from EFA_v2 import *

def EFA_step2():
  efa = EFA([])
  efa.code_level = 'machine'
  state0 = State() #Only one state code 
  efa.add_initId(state0.state_id)
  efa.add_state(state0)

  event_map = {
    "helloWorld::begin" : 0,
    "helloWorld::end" : 1
  }
  
  ################################################
  ###### Writing code for thread helloWorld ######
  ################################################
  ## Thread variable aThreadLocal using Register X16
  # Writing code for event helloWorld::begin
  tran0 = state0.writeTransition("eventCarry", state0, state0, event_map['helloWorld::begin'])
  ## Local Variable evWord using Register X17
  tran0.writeAction(f"entry: mov_imm2reg X16 0") 
  ## evw_update_event(source event word, event label, number of operands)
  tran0.writeAction(f"ev_update_1 X2 X17 {event_map['helloWorld::end']} 1") 
  tran0.writeAction(f"ev_update_1 X17 X17 0 2") 
  tran0.writeAction(f"addi X16 X16 1") 
  tran0.writeAction(f"yield") 
  
  # Writing code for event helloWorld::end
  tran1 = state0.writeTransition("eventCarry", state0, state0, event_map['helloWorld::end'])
  ##aThreadLocal--;
  tran1.writeAction(f"entry: subi X16 X16 1") 
  tran1.writeAction(f"yield") 
  
  return efa
```

The first thing to notice is around Register `X16`. This register represents the thread local variable. It is referenced in the entry of the first event `helloWorld::begin` in the `mov_imm2reg`. This instruction is the initialization of the variable. Following, we see that this variable is incremented using the `addi` instruction, and decremented later on using the `subi` instruction in the second event `helloWorld::end`.

### Step 3 - Send the event word
To send the event we will use the intrinsic function `send_event(long unsigned evWord, int unsigned netID, <type>* local data, int unsigned size, long unsigned contWord)`.

Notice that we are not considering a continuation word as part of our program (i.e. last parameter of the intrinsic function). However, this value will still be sent as part of the event. Hence, the last parameter will just be `CCONT` as placeholder. This will just forward the current continuation.

```C
thread helloWorld {
    int aThreadLocal;

    event begin() {
        aThreadLocal = 0;
        long evWord;
        // evw_update_event(Source Event Word, Event Label, Number of Operands)
        evWord = evw_update_event(CEVNT, end, 0);
        //send_event(long unsigned evWord, int unsigned netID, <type> data, long unsigned contWord)
        send_event(evWord, NETID, aThreadLocal, CCONT);
        aThreadLocal = aThreadLocal + 1;
    }

    event end() {
        aThreadLocal = aThreadLocal - 1;
    }
}
```

Let's build this program.

```bash
> ./UDweave.py -i tutorials/22March2023/HelloWorld/step3.udw -o step3.py
```

The result of this command is as follows. 

```python
from EFA_v2 import *

def EFA_step3():
  efa = EFA([])
  efa.code_level = 'machine'
  state0 = State() #Only one state code 
  efa.add_initId(state0.state_id)
  efa.add_state(state0)

  event_map = {
    "helloWorld::begin" : 0,
    "helloWorld::end" : 1
  }
  
  ################################################
  ###### Writing code for thread helloWorld ######
  ################################################
  ## Thread variable aThreadLocal using Register X16
  # Writing code for event helloWorld::begin
  tran0 = state0.writeTransition("eventCarry", state0, state0, event_map['helloWorld::begin'])
  ## Local Variable evWord using Register X17
  tran0.writeAction(f"entry: mov_imm2reg X16 0") 
  ## evw_update_event(source event word, event label, number of operands)
  tran0.writeAction(f"ev_update_1 X2 X17 {event_map['helloWorld::end']} 1") 
  tran0.writeAction(f"ev_update_1 X17 X17 0 2") 
  tran0.writeAction(f"sendr X17 X1 X0 X16 X16 0") 
  tran0.writeAction(f"addi X16 X16 1") 
  tran0.writeAction(f"yield") 
  
  # Writing code for event helloWorld::end
  tran1 = state0.writeTransition("eventCarry", state0, state0, event_map['helloWorld::end'])
  tran1.writeAction(f"entry: subi X16 X16 1") 
  tran1.writeAction(f"yield") 
  
  return  efa
```

As expected, the send_event intrinsic translated into a `sendr` instruction referring directly to X16. 

### Step 4 - Adding operand and yield_terminate

Finally, to finish this program we will receive an operand into an event. This operand will be send as part of the operand buffer registers. Also, we will add a `yield_terminate` instruction that will terminate the thread at the end of the `end()` event.

```C
thread helloWorld {
    long aThreadLocal;

    event begin(long aValue) {
        aThreadLocal = aValue;
        long evWord;
        // evw_update_event(Source Event Word, Event Label, Number of Operands)
        evWord = evw_update_event(CEVNT, end, 0);
        //send_event(long unsigned evWord, int unsigned netID, <type> data, long unsigned contWord)
        send_event(evWord, NETID, aThreadLocal, CCONT);
        aThreadLocal = aThreadLocal + 1;
    }

    event end() {
        aThreadLocal = aThreadLocal - 1;
    }
}
```

Building the program:

```bash
> ./UDweave.py -i tutorials/22March2023/HelloWorld/step4.udw -o step4.py
```


And the result
```python
from EFA_v2 import *

def EFA_step4():
  efa = EFA([])
  efa.code_level = 'machine'
  state0 = State() #Only one state code 
  efa.add_initId(state0.state_id)
  efa.add_state(state0)


  event_map = {
    "helloWorld::begin" : 0,
    "helloWorld::end" : 1
  }

  
  ################################################
  ###### Writing code for thread helloWorld ######
  ################################################
  ## Thread variable aThreadLocal using Register X16
  # Writing code for event helloWorld::begin
  tran0 = state0.writeTransition("eventCarry", state0, state0, event_map['helloWorld::begin'])
  ## Param aValue using Register X8
  ## Local Variable evWord using Register X17
  tran0.writeAction(f"entry: mov_imm2reg X16 0") 
  ## evw_update_event(source event word, event label, number of operands)
  tran0.writeAction(f"ev_update_1 X2 X17 {event_map['helloWorld::end']} 1") 
  tran0.writeAction(f"ev_update_1 X17 X17 0 2") 
  tran0.writeAction(f"sendr X17 X1 X0 X16 X16 0") 
  tran0.writeAction(f"addi X16 X16 1") 
  tran0.writeAction(f"yield") 
  
  # Writing code for event helloWorld::end
  tran1 = state0.writeTransition("eventCarry", state0, state0, event_map['helloWorld::end'])
  tran1.writeAction(f"entry: subi X16 X16 1") 
  tran1.writeAction(f"yield") 
  
  return efa
```

The value of `aValue` will be available in register `X8`.